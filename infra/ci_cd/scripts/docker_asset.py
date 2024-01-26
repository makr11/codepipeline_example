import docker
import dirhash
import boto3

import argparse
import os
from pathlib import Path

client = docker.from_env()
ecr_client = boto3.client('ecr')


def main(dockerfile_dir, ecr_repo_name, account, region):
    # Create directory fingerprint
    dockerfile_path = str(Path(__file__).parent.parent.parent.parent / dockerfile_dir)
    image_tag = dirhash.dirhash(dockerfile_path, 'md5')
    with open(f"{Path(__file__).parent}/.env", "w") as f:
        f.write(f"IMAGE_TAG={image_tag}")

    # Build the Docker image if image does not exist
    image_not_found = os.system(f"aws ecr describe-images --repository-name {ecr_repo_name} --image-ids imageTag={image_tag} --region {region} --output table --no-cli-pager")
    if image_not_found:
        _, build_logs = client.images.build(
            path=dockerfile_path,
            tag=f"{account}.dkr.ecr.{region}.amazonaws.com/{ecr_repo_name}:{image_tag}"
        )

        # Print the build logs
        for log in build_logs:
            print(log.get('stream', '').strip())

        # Push the image to ecr repository
        os.system(f"aws ecr get-login-password --region {region} | docker login --username AWS --password-stdin {account}.dkr.ecr.{region}.amazonaws.com")
        push_logs = client.images.push(
            repository=f"{account}.dkr.ecr.{region}.amazonaws.com/{ecr_repo_name}",
            tag=image_tag
        )

        # Print the push logs
        print(push_logs)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('dockerfile_dir', type=str, help='Path to the directory containing Dockerfile')
    parser.add_argument('ecr_repo_name', type=str, help='Name of the ECR repository')
    parser.add_argument('account', type=str, help='AWS account number')
    parser.add_argument('region', type=str, help='Name of the region')
    args = parser.parse_args()
    main(args.dockerfile_dir, args.ecr_repo_name, args.account, args.region)
