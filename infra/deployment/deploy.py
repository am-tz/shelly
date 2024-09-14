# Internal libs
from infra.deployment.pack import pack
from infra.deployment.shell import Shell
from infra.log.setup import LoggingSetup

# General utilities
from sys import argv
from subprocess import run
from typing import List
import argparse


def main():

    LoggingSetup()

    parser = argparse.ArgumentParser(description='Script to deploy latest code version to the robot.')
    parser.add_argument('--host', required=True, type=str, help='The host address')
    parser.add_argument('--user', required=True, type=str, help='The username for authentication')
    parser.add_argument('--password', required=True, type=str, help='The password for authentication')
    parser.add_argument('--path', required=True, type=str, help='The directory path of the repo on the robot')
    parser.add_argument('--updateReqs', required=False, type=bool, help='(Re-)install the python requirements.txt')
    mode_help: str = 'Either "git" for a push here and pull on the robot, or "zip" for a simple overwrite via ssh'
    parser.add_argument('--mode', required=True, type=str, choices=['git', 'zip'], help=mode_help)
    args = parser.parse_args()

    destination = f"{args.user}@{args.host}:{args.path}"
    print(f"Updating {destination} via {args.mode}..")

    shell_commands: List[str] = []

    if args.mode == 'git':
        run("git push")
        shell_commands = [
            "cd ~/Desktop/shelly",
            "git pull"
        ]
    elif args.mode == 'zip':
        zip_file_path: str = pack()
        run(f"pscp -pw {args.password} {zip_file_path} {destination}")

        shell_commands = [
            "cd ~/Desktop",
            "ls",
            "rm -r shelly -f",
            "ls",
            "unzip shelly.zip",
            "cd shelly"
        ]

    if args.updateReqs:
        shell_commands += [
            "python -m venv ~/Desktop/shelly/.venv",
            "source ./.venv/bin/activate",
            "pip install -r requirements.txt"
        ]

    shell_commands += ["exit"]

    shell = Shell(args.host, args.password, args.user)
    shell.execute(shell_commands)


if __name__ == '__main__':
    main()
