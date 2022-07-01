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

https://github.com/samimcloud2020/weaveflux-k8s-code.git
https://github.com/samimcloud2020/weaveflux-k8s-manifest.git
Enter a value for Token description, check the repo permission scope and scroll down and click the Generate token button
github ----> settings--->developer setting----> personal access token ---> give access to Repo only & generate a TOKEN.

                                           INSTALL WEAVE FLUX
Now we will use Helm to install Weave Flux into our cluster and enable it to interact with our Kubernetes configuration GitHub repo.

First, install the Flux Custom Resource Definition:

kubectl apply -f https://raw.githubusercontent.com/fluxcd/helm-operator/master/deploy/crds.yaml
Check that Helm is installed.

helm list
This command should either return a list of helm charts that have already been deployed or nothing.

set ENVIOURNMENT Variable
YOURUSER=yourgitusername

First, create the flux Kubernetes namespace

kubectl create namespace flux
Next, add the Flux chart repository to Helm and install Flux.

helm repo add fluxcd https://charts.fluxcd.io

helm upgrade -i flux fluxcd/flux \
--set git.url=git@github.com:${YOURUSER}/k8s-config \
--set git.branch=main \
--namespace flux

helm upgrade -i helm-operator fluxcd/helm-operator \
--set helm.versions=v3 \
--set git.ssh.secretName=flux-git-deploy \
--set git.branch=main \
--namespace flux

Watch the install and confirm everything starts. There should be 3 pods.

kubectl get pods -n flux
Install fluxctl in order to get the SSH key to allow GitHub write access. This allows Flux to keep the configuration in GitHub in sync with the configuration deployed in the cluster.

sudo wget -O /usr/local/bin/fluxctl $(curl https://api.github.com/repos/fluxcd/flux/releases/latest | jq -r ".assets[] | select(.name | test(\"linux_amd64\")) | .browser_download_url")
sudo chmod 755 /usr/local/bin/fluxctl

fluxctl version
fluxctl identity --k8s-fwd-ns flux

Copy the provided key and add that as a deploy key in the GitHub repository.

In GitHub, select your k8s-config GitHub repo. Go to Settings and click Deploy Keys. Alternatively, you can go by direct URL by replacing your user name in this URL: github.com/YOURUSER/k8s-config/settings/keys.
Click on Add Deploy Key
Name: Flux Deploy Key
Paste the key output from fluxctl
Click Allow Write Access. This allows Flux to keep the repo in sync with the real state of the cluster
Click Add Key


Now Flux is configured and should be ready to pull configuration.

CREATE IMAGE WITH CODEPIPELINE
cloudformation template in yaml for codepipeline with eks

---
AWSTemplateFormatVersion: 2010-09-09

Description: CFN Template to deploy CodePipeline to build Docker Image and push to ECR

Parameters:

  GitSourceRepo:
    Type: String
    Description: GitHub source repository - must contain a Dockerfile in the base
    Default: eks-example
    MinLength: 1
    MaxLength: 100
    ConstraintDescription: You must enter a GitHub repository name

  GitBranch:
    Type: String
    Default: main
    Description: GitHub git repository branch - change triggers a new build
    MinLength: 1
    MaxLength: 100
    ConstraintDescription: You must enter a GitHub repository branch name

  GitHubToken:
    Type: String
    NoEcho: true
    Description: GitHub API token from https://github.com/settings/tokens
    MinLength: 3
    MaxLength: 100
    ConstraintDescription: You must enter a GitHub personal access token

  GitHubUser:
    Type: String
    Description: GitHub username or organization
    MinLength: 3
    MaxLength: 100
    ConstraintDescription: You must enter a GitHub username or organization

Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: GitHub
        Parameters:
          - GitHubUser
          - GitHubToken
          - GitSourceRepo
          - GitBranch
    ParameterLabels:
      GitHubUser:
        default: Username
      GitHubToken:
        default: Access token
      GitSourceRepo:
        default: Repository
      GitBranch:
        default: Branch

Resources:

  EcrDockerRepository:
    Type: AWS::ECR::Repository
    DeletionPolicy: Retain
    Properties:
      RepositoryName: !Ref GitSourceRepo

  #CodePipelineArtifactBucket:
  #  Type: AWS::S3::Bucket
  #  DeletionPolicy: Retain

  #CodePipelineServiceRole:
  #  Type: AWS::IAM::Role
  #  Properties:
  #    Path: /
  #    AssumeRolePolicyDocument:
  #      Version: 2012-10-17
  #      Statement:
  #        - Effect: Allow
  #          Principal:
  #            Service: codepipeline.amazonaws.com
  #          Action: sts:AssumeRole
  #    Policies:
  #      - PolicyName: codepipeline-access
  #        PolicyDocument:
  #          Version: 2012-10-17
  #          Statement:
  #            - Resource: "*"
  #              Effect: Allow
  #              Action:
  #                - codebuild:StartBuild
  #                - codebuild:BatchGetBuilds
  #                - codecommit:GetBranch
  #                - codecommit:GetCommit
  #                - codecommit:UploadArchive
  #                - codecommit:GetUploadArchiveStatus
  #                - codecommit:CancelUploadArchive
  #                - iam:PassRole
  #            - Resource: !Sub arn:aws:s3:::${CodePipelineArtifactBucket}/*
  #              Effect: Allow
  #              Action:
  #                - s3:PutObject
  #                - s3:GetObject
  #                - s3:GetObjectVersion
  #                - s3:GetBucketVersioning
  #  DependsOn: CodePipelineArtifactBucket

  #CodeBuildServiceRole:
  #  Type: AWS::IAM::Role
  #  Properties:
  #    Path: /
  #    AssumeRolePolicyDocument:
  #      Version: 2012-10-17
  #      Statement:
  #        - Effect: Allow
  #          Principal:
  #            Service: codebuild.amazonaws.com
  #          Action: sts:AssumeRole
  #    Policies:
  #      - PolicyName: root
  #        PolicyDocument:
  #          Version: 2012-10-17
  #          Statement:
  #            - Resource: '*'
  #              Effect: Allow
  #              Action:
  #                - logs:CreateLogGroup
  #                - logs:CreateLogStream
  #                - logs:PutLogEvents
  #            - Resource: '*'
  #              Effect: Allow
  #              Action:
  #                - ecr:GetAuthorizationToken
  #            - Resource: !Sub arn:aws:s3:::${CodePipelineArtifactBucket}/*
  #              Effect: Allow
  #              Action:
  #                - s3:GetObject
  #                - s3:PutObject
  #                - s3:GetObjectVersion
  #            - Resource: !Sub arn:aws:ecr:${AWS::Region}:${AWS::AccountId}:repository/${EcrDockerRepository}
  #              Effect: Allow
  #              Action:
  #                - ecr:GetDownloadUrlForLayer
  #                - ecr:BatchGetImage
  #                - ecr:BatchCheckLayerAvailability
  #                - ecr:PutImage
  #                - ecr:InitiateLayerUpload
  #                - ecr:UploadLayerPart
  #                - ecr:CompleteLayerUpload

  CodeBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Artifacts:
        Type: CODEPIPELINE
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          phases:
            install:
              runtime-versions:
                docker: 18
              commands:
                - curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
                - apt-get -y update
                - apt-get -y install jq
            pre_build:
              commands:
                - echo "Starting docker daemon..."
                - nohup /usr/local/bin/dockerd --host=unix:///var/run/docker.sock --host=tcp://127.0.0.1:2375 --storage-driver=overlay2&
                - timeout 15 sh -c "until docker info; do echo .; sleep 1; done"
                - echo "Logging into Amazon ECR..."
                - $(aws ecr get-login --no-include-email --region ${AWS_DEFAULT_REGION})
                - TAG="$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | head -c 8)"
            build:
              commands:
                - echo Build started on `date`
                - docker build -t "${REPOSITORY_URI}:latest" .
                - docker tag "${REPOSITORY_URI}:latest" "${REPOSITORY_URI}:${TAG}"
            post_build:
              commands:
                - echo Build completed on `date`
                - echo "Pushing Docker image to ECR"
                - docker push "${REPOSITORY_URI}:latest"
                - docker push "${REPOSITORY_URI}:${TAG}"
                - printf '{"Tag":"%s","RepositoryUri":"%s"}' $TAG $REPOSITORY_URI $PROJECT_NAME $ARTIFACT_BUCKET > build.json
      Environment:
        ComputeType: BUILD_GENERAL1_SMALL
        Type: LINUX_CONTAINER
        Image: "aws/codebuild/standard:2.0"
        PrivilegedMode: True
        EnvironmentVariables:
          - Name: AWS_DEFAULT_REGION
            Value: !Ref AWS::Region
          - Name: REPOSITORY_URI
            Value: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${EcrDockerRepository}
      Name: !Ref AWS::StackName
      ServiceRole: !Sub arn:aws:iam::${AWS::AccountId}:role/eksworkshop-CodeBuildServiceRole

  CodePipelineGitHub:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      RoleArn: !Sub arn:aws:iam::${AWS::AccountId}:role/eksworkshop-CodePipelineServiceRole
      ArtifactStore:
        Type: S3
        Location: !Sub eksworkshop-${AWS::AccountId}-codepipeline-artifacts
      Stages:
        - Name: Source
          Actions:
            - Name: App
              ActionTypeId:
                Category: Source
                Owner: ThirdParty
                Version: 1
                Provider: GitHub
              Configuration:
                Owner: !Ref GitHubUser
                Repo: !Ref GitSourceRepo
                Branch: !Ref GitBranch
                OAuthToken: !Ref GitHubToken
              OutputArtifacts:
                - Name: App
              RunOrder: 1
        - Name: Build
          Actions:
            - Name: Build
              ActionTypeId:
                Category: Build
                Owner: AWS
                Version: 1
                Provider: CodeBuild
              Configuration:
                ProjectName: !Ref CodeBuildProject
              InputArtifacts:
                - Name: App
              OutputArtifacts:
                - Name: BuildOutput
              RunOrder: 1
    DependsOn: CodeBuildProject
git clone https://github.com/${YOURUSER}/eks-example.git
cd eks-example
Next create a base README file, a source directory, and download a sample nginx configuration (hello.conf), home page (index.html), and Dockerfile.

echo "# eks-example" > README.md
mkdir src
wget -O src/hello.conf https://raw.githubusercontent.com/aws-samples/eks-workshop/main/content/intermediate/260_weave_flux/app.files/hello.conf
wget -O src/index.html https://raw.githubusercontent.com/aws-samples/eks-workshop/main/content/intermediate/260_weave_flux/app.files/index.html
wget https://raw.githubusercontent.com/aws-samples/eks-workshop/main/content/intermediate/260_weave_flux/app.files/Dockerfile
Now that we have a simple hello world app, commit the changes to start the image build pipeline.

git add .
git commit -am "Initial commit"
git push 


DEPLOY FROM MANIFESTS
Now we are ready to use Weave Flux to deploy the hello world application into our Amazon EKS cluster. To do this we will clone our GitHub config repository (k8s-config) and then commit Kubernetes manifests to deploy.

cd ..
git clone https://github.com/${YOURUSER}/k8s-config.git     
cd k8s-config
mkdir charts namespaces releases workloads
Create a namespace Kubernetes manifest.

cat << EOF > namespaces/eks-example.yaml
apiVersion: v1
kind: Namespace
metadata:
  labels:
    name: eks-example
  name: eks-example
EOF
Create a deployment Kubernetes manifest.
cat << EOF > workloads/eks-example-dep.yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: eks-example
  namespace: eks-example
  labels:
    app: eks-example
  annotations:
    # Container Image Automated Updates
    flux.weave.works/automated: "true"
    # do not apply this manifest on the cluster
    #flux.weave.works/ignore: "true"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: eks-example
  template:
    metadata:
      labels:
        app: eks-example
    spec:
      containers:
      - name: eks-example
        image: YOURACCOUNT.dkr.ecr.us-east-1.amazonaws.com/eks-example:YOURTAG
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 80
          name: http
          protocol: TCP
        livenessProbe:
          httpGet:
            path: /
            port: http
        readinessProbe:
          httpGet:
            path: /
            port: http
EOF
Above you see 2 Kubernetes annotations for Flux.

flux.weave.works/automated tells Flux whether the container image should be automatically updated.
flux.weave.works/ignore is commented out, but could be used to tell Flux to temporarily ignore the deployment.
Finally, create a service manifest to enable a load balancer to be created.

cat << EOF > workloads/eks-example-svc.yaml
apiVersion: v1
kind: Service
metadata:
  name: eks-example
  namespace: eks-example
  labels:
    app: eks-example
spec:
  type: LoadBalancer
  ports:
    - port: 80
      targetPort: http
      protocol: TCP
      name: http
  selector:
    app: eks-example
EOF
Now commit the changes and push to your repository.

git add . 
git commit -am "eks-example-deployment"
git push 
Check the logs of your Flux pod. It will pull config from the k8s-config repository every 5 minutes. Ensure you replace the pod name below with the name in your deployment.

kubectl get pods -n flux

kubectl logs flux-5bd7fb6bb6-4sc78 -n flux
Now get the URL for the load balancer (LoadBalancer Ingress) and connect via your browser (this may take a couple minutes for DNS).

kubectl describe service eks-example -n eks-example
Make a change to the eks-example source code and push a new change.

cd ../eks-example
vi src/index.html
   # Change the <title> AND <h> to Hello World Version 2

git commit -am "v2 Updating home page"
git push
Now you can watch in the CodePipeline console for the new image build to complete. This will take a couple minutes. Once complete, you will see a new image land in your Amazon ECR repository. Monitor the kubectl logs for the Flux pod and you should see it update the configuration within five minutes.

Verify the web page has updated by refreshing the page in your browser.

Your boss calls you late at night and tells you that people are complaining about the deployment. We need to back it out immediately! We could modify the code in eks-example and trigger a new image build and deploy. However, we can also use git to revert the config change in k8s-config. Lets take that approach.

cd ../k8s-config
git pull 

git log --oneline

git revert HEAD
   # Save the commit message

git log --oneline 

git push
You should now be able to watch logs for the Flux pod and it will pull the config change and roll out the previous image. Check your URL in the browser to ensure it is reverted.
