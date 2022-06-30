# weaveflux-k8s-manifest
helm version
AWS CodePipeline and AWS CodeBuild both need AWS Identity and Access Management (IAM) service roles to create a Docker image build pipeline.

In this step, we are going to create an IAM role and add an inline policy that we will use in the CodeBuild stage to interact with the EKS cluster via kubectl.

Create the bucket and roles:
# Use your account number below
ACCOUNT_ID=$(aws sts get-caller-identity | jq -r '.Account')
aws s3 mb s3://eksworkshop-${ACCOUNT_ID}-codepipeline-artifacts
mkdir enviournment
cd ~/environment

wget https://eksworkshop.com/intermediate/260_weave_flux/iam.files/cpAssumeRolePolicyDocument.json

aws iam create-role --role-name eksworkshop-CodePipelineServiceRole --assume-role-policy-document file://cpAssumeRolePolicyDocument.json 

wget https://eksworkshop.com/intermediate/260_weave_flux/iam.files/cpPolicyDocument.json

aws iam put-role-policy --role-name eksworkshop-CodePipelineServiceRole --policy-name codepipeline-access --policy-document file://cpPolicyDocument.json

wget https://eksworkshop.com/intermediate/260_weave_flux/iam.files/cbAssumeRolePolicyDocument.json

aws iam create-role --role-name eksworkshop-CodeBuildServiceRole --assume-role-policy-document file://cbAssumeRolePolicyDocument.json 

wget https://eksworkshop.com/intermediate/260_weave_flux/iam.files/cbPolicyDocument.json

aws iam put-role-policy --role-name eksworkshop-CodeBuildServiceRole --policy-name codebuild-access --policy-document file://cbPolicyDocument.json

We are going to create 2 GitHub repositories. One will be used for a sample application that will trigger a Docker image build. Another will be used to hold Kubernetes manifests that Weave Flux deploys into the cluster. Note this is a pull based method compared to other continuous deployment tools that push to Kubernetes.


