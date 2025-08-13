- Recreate requirements.txt with hashes / create the requirements-build.txt
```
podman run --rm -ti -v $PWD:$PWD:z -w "$PWD" --entrypoint /bin/bash quay.io/konflux-ci/hermeto:latest
```

- In the container run the following:
```
dnf -y install python3.12-pip
pip3.12 install pip-tools pybuild-deps
sed -i '22i "patchelf==0.11.0",' kai_mcp_solution_server/pyproject.toml #numpy needs this and it doesn't get pulled down for some reason
cd kai_mcp_solution_server
pip-compile --no-annotate --generate-hashes --output-file=requirements.txt pyproject.toml
pybuild-deps compile --generate-hashes --output-file=requirements-build.txt requirements.txt
```

- In requirements.txt replace:
  - jiter:
```
jiter==0.10.0 \
    --hash=sha256:023aa0204126fe5b87ccbcd75c8a0d0261b9abdbbf46d55e7ae9f8e22424eeb8 \
...
```
with:
```
jiter @ https://github.com/jmontleon/jiter/archive/refs/heads/main.tar.gz \
    --hash=sha256:14b1bf683b341d9ae78d9ec625757108a025750bc63b940b3183b96b1c366a0d
```

  - tiktoken
```
tiktoken==0.9.0 \
    --hash=sha256:03935988a91d6d3216e2ec7c645afbb3d870b37bcb67ada1943ec48678e7ee33 \
...
```
with:
```
tiktoken @ https://github.com/jmontleon/tiktoken/archive/refs/heads/main.tar.gz \
    --hash=sha256:d9ad52c4e2ff5f04873285c2b19a83ff7aad29da72ab1ab9ab16b838bf14ff5c
```

  - pydantic-core:
```
pydantic-core==2.33.2 \
    --hash=sha256:0069c9acc3f3981b9ff4cdfaf088e98d83440a4c7ea1bc07460af3d4dc22e72d \
...
```
with:
```
pydantic-core @ https://github.com/jmontleon/pydantic_core/archive/refs/heads/main.tar.gz \
    --hash=sha256:ca5e5f0655dcd7425f5378bb57b9faaccbc91d8ce04063ca001eec2fb0786376
```

  - zstandard
```
zstandard==0.23.0 \
    --hash=sha256:034b88913ecc1b097f528e42b539453fa82c3557e414b3de9d5632c80439a473 \
...
```
with:
```
zstandard @ https://github.com/jmontleon/zstandard/archive/refs/heads/main.tar.gz \
    --hash=sha256:4bd4b4d415105f18da4d3256975fb070833bb30268839f2204ebc9295d1da5b6
```

- In requirements-build.txt replace:
  - maturin
```
maturin==1.9.3 \
    --hash=sha256:267ac8d0471d1ee2320b8b2ee36f400a32cd2492d7becbd0d976bd3503c2f69b \
...
```
with:
```
maturin @ https://github.com/jmontleon/maturin/archive/refs/heads/main.tar.gz \
    --hash=sha256:7009568c272569a73d0c6b9861af6a5705d4e0506a730b6fbeccf4917833da84
```

- Exit the container.

- Restore pyproject.toml for next steps
```
git checkout kai_mcp_solution_server/pyproject.toml
```

- Build a container with workarounds for cargo
```
podman build -f kai_mcp_solution_server/Containerfile.hermeto-workaround -t quay.io/konflux-ci/hermeto:workaround kai_mcp_solution_server
```
- Collect deps
```
podman run --rm -ti -v $PWD:$PWD:z -w "$PWD" quay.io/konflux-ci/hermeto:workaround --mode permissive fetch-deps --source . '{"packages": [{"type": "pip", "path": "kai_mcp_solution_server"}], "flags": []}'
```

- Inject files
```
podman run --rm -ti -v $PWD:$PWD:z -w "$PWD" quay.io/konflux-ci/hermeto:workaround inject-files --for-output-dir /app/hermeto-output hermeto-output
```

- Create Containerfile.test
```
podman build -f kai_mcp_solution_server/Containerfile.test -t kai_mcp_solution_server:offline-build kai_mcp_solution_server
```

- Start the build offline container
```
podman run -it --entrypoint /bin/bash --network=none -v $PWD:/app:z kai_mcp_solution_server:offline-build
```

- Within the container run:
```
#tree sitter java madness
pushd /app/hermeto-output/deps/pip/
tar zxvf tree-sitter-0.24.0.tar.gz
mkdir /usr/include/tree_sitter
cp /app/hermeto-output/deps/pip/tree-sitter-0.24.0/tree_sitter/core/lib/src/parser.h /usr/include/tree_sitter
popd
```

```
sed -i -e '25,28d' kai_mcp_solution_server/pyproject.toml
pip3.12 install --no-cache-dir ./kai_mcp_solution_server
```
