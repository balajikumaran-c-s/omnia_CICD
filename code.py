import subprocess

BUILD_PARAMS_FILE = "/root/automation/build_params.txt"
REPO_URL = "https://github.com/dell/omnia-artifactory.git"
BRANCH = "omnia-container"
TARGET_DIR = "/build_image"


def read_build_params(file_path=BUILD_PARAMS_FILE):
    """Read key=value pairs from build_params.txt."""
    params = {}
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                key, value = line.split("=", 1)
                params[key.strip()] = value.strip()
    return params


def run_remote_cmd(cmd, host, user, password):
    """Run a remote command using sshpass + SSH."""
    ssh_command = f'sshpass -p "{password}" ssh -o StrictHostKeyChecking=no {user}@{host} "{cmd}"'
    result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] {cmd}\n{result.stderr}")
    else:
        print(result.stdout)


def prepare_and_clone(host, user, password):
    """Remove target directory, recreate it, and clone repository."""
    print(f"Removing {TARGET_DIR} on {host} (if any)...")
    run_remote_cmd(f"sudo rm -rf {TARGET_DIR}", host, user, password)

    print(f"Creating {TARGET_DIR} on {host}...")
    run_remote_cmd(f"sudo mkdir -p {TARGET_DIR}", host, user, password)

    print(f"Cloning {BRANCH} branch into {TARGET_DIR}...")
    run_remote_cmd(f"sudo git clone --branch {BRANCH} {REPO_URL} {TARGET_DIR}", host, user, password)


def build_images(host, user, password, images, branch):
    """Run build_image.sh on the remote host for given images and branch."""
    if not images:
        print("No images to build.")
        return

    # Join image names into a single string
    cmd = f"cd {TARGET_DIR} && sudo sh build_images.sh {images} omnia_branch={branch}"

    print(f"Running build_image.sh on {host} for images: {images} with omnia_branch={branch}")
    run_remote_cmd(cmd, host, user, password)


if __name__ == "__main__":
    # Read parameters from build_params.txt
    build_params = read_build_params()

    REMOTE_HOST = build_params.get("SERVER_IP")
    USERNAME = build_params.get("SERVER_USER")
    PASSWORD = build_params.get("SERVER_PASS", "dell")
    BUILD_METHOD = build_params.get("BUILD_METHOD")
    IMAGES = build_params.get("IMAGES")
    OMNIA_BRANCH = build_params.get("OMNIA_BRANCH")
    print(f"=== Build Parameters ===")
    print(f"Host: {REMOTE_HOST}")
    print(f"User: {USERNAME}")
    print(f"Build Method: {BUILD_METHOD}")
    print(f"Images: {IMAGES}")
    print(f"branch: {OMNIA_BRANCH}")

    # Run preparation and clone
    prepare_and_clone(REMOTE_HOST, USERNAME, PASSWORD)
    print(f"Repository successfully cloned to {TARGET_DIR} on {REMOTE_HOST}")

    # Run build images only if build method is omnia-artifactory
    if BUILD_METHOD == "omnia-artifactory":
        build_images(REMOTE_HOST, USERNAME, PASSWORD, IMAGES, OMNIA_BRANCH)
    else:
        print(f"Build method '{BUILD_METHOD}' is not implemented yet.")

