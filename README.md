# troposphere-demo

An example of usage [troposphere](https://github.com/cloudtools/troposphere) for generation
of [Cloud Formation](https://aws.amazon.com/cloudformation/) templates.

Example contains template which can be used for generation of [VPC](https://aws.amazon.com/vpc/) with 3 following
multi-az subnets:

- `Public` (Outbound internet access)
- `Private` (No internet access)
- `Protected` (Outbound internet access via NAT)

VPC Cidr as well as "DNS Hostnames" parameter can be configured
via [Cloud Formation Parameters](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/parameters-section-structure.html)
.

Template can be reused for creation of different environments, see [usage](#usage) section.

Generated templates could be validated using [cfn-guard](https://github.com/aws-cloudformation/cloudformation-guard)
util against predefined rules(e.g. to ensure that all
resources [contain set of mandatory tags](./validation/mandatory_tags.ruleset) for billing purposes)

## Usage

Requirements:

- [Python 3.9](https://www.python.org/) (may work on lower version, but not tested yet)
- [Pip](https://pypi.org/project/pip/)
- [Brew](https://brew.sh/) (used for installation of `cfn-guard`, `pre-commit`)

```shell
make help # Print help

make setup # Setup (Mac OS only)

make dep # Download dependencies

make generate # Generate Cloud Formation template

aws cloudformation create-stack --stackname mystack # Deploy created template to dev env
--template-body file:///$(pwd)/templates/output/resources.yaml
--parameters file:///$(pwd)/envs/dev.json
```

## Development

See [CONTRIBUTING.md](./CONTRUBUTING.md) for code style and tooling.

## TODO

- [ ] E2E testing with [taskcat](https://github.com/aws-quickstart/taskcat)
- [ ] Establish naming convention for resources and setup validation rules for it
- [ ] Move dynamic part of template from Cloudformation to Troposphere(?)
- [ ] Extend example with [sceptre](https://github.com/Sceptre/sceptre) for managing Cloudformation stacks
- [ ] Add diagram of created arch

## Refs

- https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/best-practices.html
- https://github.com/aws-cloudformation/cloudformation-guard
- https://github.com/Sceptre/sceptre
- https://github.com/alexgibs/cfnstyle
- https://www.proud2becloud.com/troposphere-a-better-way-to-build-manage-and-maintain-a-cloudformation-based-infrastructure-on-aws/
- https://troposphere.readthedocs.io/en/latest/quick_start.html
- https://www.cloudavail.com/blog/2016/05/23/creating-vpcs-and-subnets-across-regions-with-a-single-cloudformation-file
- https://github.com/aws-cloudformation/cfn-lint
