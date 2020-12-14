import os
import shlex
import subprocess
import time


def upload(keyname, ip_address, upload_dir="./code/upload"):
    """upload code to the instance"""
    permission_cmd = f"chmod 600 {keyname}.pem"
    print(permission_cmd)
    permissions_token = shlex.split(permission_cmd)
    permission_process = subprocess.Popen(
        permissions_token, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    perm_stdout, perm_stderr = permission_process.communicate()
    time.sleep(10)
    upload_cmd = f"scp -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -r -i {keyname}.pem {upload_dir}/ ubuntu@{ip_address}:/home/ubuntu/"
    print(upload_cmd)
    upload_token = shlex.split(upload_cmd)
    process = subprocess.Popen(upload_token,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    stdout, stderr
    return (stdout, stderr)


def ssh_execute(keyname, ip_address):
    ssh_cmd = f"ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i {keyname}.pem ubuntu@{ip_address}"
    print(ssh_cmd)
    ssh_token = shlex.split(ssh_cmd)
    ssh = subprocess.Popen(ssh_token,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           universal_newlines=True,
                           bufsize=0)

    # Send ssh commands to stdin
    ssh.stdin.write("cd upload\n")
    ssh.stdin.write("chmod +x config.sh\n")
    ssh.stdin.write("./config.sh\n")
    ssh.stdin.close()

    # Fetch output
    for line in ssh.stdout:
        if line == "END\n":
            break
        print(line, end="")


if __name__ == "__main__":
    upload("ec2-auto", "54.236.48.171", upload_dir="./code/test_upload")
    # ssh_execute("ec2-auto", "54.236.48.171")
