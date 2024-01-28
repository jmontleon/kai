#!/usr/bin/env python

import os
import subprocess  # trunk-ignore(bandit)
import sys

sample_source_apps = {
    "sample_repos/eap-coolstore-monolith": "eap-coolstore-monolith",
    "sample_repos/helloworld-mdb": "helloworld-mdb",
    "sample_repos/kitchensink": "kitchensink",
    "sample_repos/ticket-monster": "ticket-monster",
    "sample_repos/jboss-eap-quickstarts/bmt-to-quarkus": "bmt-to-quarkus",
    "sample_repos/jboss-eap-quickstarts/cmt-to-quarkus": "cmt-to-quarkus",
    "sample_repos/jboss-eap-quickstarts/ejb-remote-to-quarkus-rest": "ejb-remote-to-quarkus-rest",
    "sample_repos/jboss-eap-quickstarts/ejb-security-to-quarkus-basic-elytron": "ejb-security-to-quarkus-basic-elytron",
    "sample_repos/jboss-eap-quickstarts/tasks-qute": "tasks-qute",
}


def ensure_kantra_bin_exists():
    kantra_bin = os.path.join(os.getcwd(), "bin/kantra")
    if not os.path.isfile(kantra_bin):
        sys.exit(f"Unable to find {kantra_bin}\nPlease install Kantra")


def ensure_output_dir_exists(output_dir):
    if not os.path.isdir(output_dir):
        os.mkdir(output_dir)


def analyze_all():
    ensure_kantra_bin_exists()
    for source_dir, output_dir in sample_source_apps.items():
        full_output_dir = os.path.join(os.getcwd(), f"analysis_reports/{output_dir}")
        ensure_output_dir_exists(full_output_dir)
        print(f"Analyzing '{source_dir}', will write output to '{full_output_dir}'")
        cmd = f'time ./bin/kantra analyze -i {source_dir} -t "quarkus" -t "jakarta-ee" -t "jakarta-ee8+" -t "jakarta-ee9+" -t "cloud-readiness" -o {full_output_dir} --overwrite'
        subprocess.run(cmd, shell=True)  # trunk-ignore(bandit)


if __name__ == "__main__":
    analyze_all()
