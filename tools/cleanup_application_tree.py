# coding: utf-8
"""
Remove files from the package that are not needed and too big.
This script can be launched after PyInstaller and before installers creation.
"""
import os
import shutil
import sys
from pathlib import Path
from typing import Generator, List, Tuple

FILES: Tuple[str] = (
    "PyQt*/Qt/lib",  # Contains only WebEngineCore.framework on macOS
    "PyQt*/Qt/plugins/mediaservice",
    "PyQt*/Qt/plugins/position",
    "PyQt*/Qt/plugins/printsupport",
    "PyQt*/Qt/plugins/sensorgestures",
    "PyQt*/Qt/plugins/sensors",
    "PyQt*/Qt/plugins/sqldrivers",
    "PyQt*/Qt/qml/Qt/labs/location",
    "PyQt*/Qt/qml/Qt/WebSockets",
    "PyQt*/Qt/qml/QtAudioEngine",
    "PyQt*/Qt/qml/QtBluetooth",
    "PyQt*/Qt/qml/QtCanvas3D",
    "PyQt*/Qt/qml/QtGraphicalEffects",
    "PyQt*/Qt/qml/QtLocation",
    "PyQt*/Qt/qml/QtMultimedia",
    "PyQt*/Qt/qml/QtNfc",
    "PyQt*/Qt/qml/QtPositioning",
    "PyQt*/Qt/qml/QtQml/RemoteObjects",
    "PyQt*/Qt/qml/QtQuick/Controls.2/designer",
    "PyQt*/Qt/qml/QtQuick/Extras/designer",
    "PyQt*/Qt/qml/QtQuick/Particles.2",
    "PyQt*/Qt/qml/QtQuick/Scene2D",
    "PyQt*/Qt/qml/QtQuick/Scene3D",
    "PyQt*/Qt/qml/QtSensors",
    "PyQt*/Qt/qml/QtTest",
    "PyQt*/Qt/qml/QtWebChannel",
    "PyQt*/Qt/qml/QtWebEngine",
    "PyQt*/Qt/qml/QtWebSockets",
    "PyQt*/QtPositioning.*",
    "PyQt*/QtPrintSupport.*",
    "PyQt*/QtSensors.*",
    "PyQt*/QtSerialPort.*",
    "PyQt*/QtTest.*",
    "PyQt*/Qt/translations/qtdeclarative*",
    "PyQt*/Qt/translations/qt_help*",
    "PyQt*/Qt/translations/qtmultimedia*",
    "PyQt*/Qt/translations/qtserialport*",
    "PyQt*/QtBluetooth.*",
    # "PyQt*/QtDBus.*",
    "PyQt*/QtDesigner.*",
    "PyQt*/QtHelp.*",
    "PyQt*/QtLocation.*",
    "PyQt*/QtMacExtras.*",
    "PyQt*/QtMultimedia*.*",
    "PyQt*/QtNfc.*",
    "PyQt*/QtSql.*",
    "PyQt*/QtWebChannel.*",
    "PyQt*/QtWebEngine*.*",
    "PyQt*/QtWebSockets.*",
    "PyQt*/QtXmlPatterns.*",
    "PyQt*/QtXml.*",
    "*Qt*Bluetooth*",
    "*Qt*Concurrent*",
    # "*Qt*DBus*",
    "*Qt*Designer*",
    "*Qt*Help*",
    "*Qt*Location*",
    "*Qt*MacExtras*",
    "*Qt*Multimedia*",
    "*Qt*Nfc*",
    "*Qt*Positioning*",
    "*Qt*QuickParticles*",
    "*Qt*QuickTest*",
    "*Qt*RemoteObjects*",
    "*Qt*Sensors*",
    "*Qt*SerialPort*",
    "*Qt*Sql*",
    "*Qt*Test*",
    "*Qt*WebChannel*",
    "*Qt*WebEngine*",
    "*Qt*WebSockets*",
    "*Qt*WinExtras*",
    "*Qt*Xml*",
    "*Qt*XmlPatterns*",
    # Boto3 has useless files (only S3 is interesting for us)
    "boto3/data/cloudformation",
    "boto3/data/sns",
    "boto3/data/cloudwatch",
    "boto3/data/sqs",
    "boto3/data/dynamodb",
    "boto3/data/ec2",
    "boto3/data/glacier",
    "boto3/data/iam",
    "boto3/data/opsworks",
    "boto3/examples",
    # Botocore has a lot of useless files (only S3 is interesting for us)
    "botocore/data/accessanalyzer",
    "botocore/data/acm",
    "botocore/data/acm-pca",
    "botocore/data/alexaforbusiness",
    "botocore/data/amplify",
    "botocore/data/apigateway",
    "botocore/data/apigatewaymanagementapi",
    "botocore/data/apigatewayv2",
    "botocore/data/appconfig",
    "botocore/data/application-autoscaling",
    "botocore/data/application-insights",
    "botocore/data/appmesh",
    "botocore/data/appstream",
    "botocore/data/appsync",
    "botocore/data/athena",
    "botocore/data/autoscaling",
    "botocore/data/autoscaling-plans",
    "botocore/data/backup",
    "botocore/data/batch",
    "botocore/data/budgets",
    "botocore/data/ce",
    "botocore/data/chime",
    "botocore/data/cloud9",
    "botocore/data/clouddirectory",
    "botocore/data/cloudformation",
    "botocore/data/cloudfront",
    "botocore/data/cloudhsm",
    "botocore/data/cloudhsmv2",
    "botocore/data/cloudsearch",
    "botocore/data/cloudsearchdomain",
    "botocore/data/cloudtrail",
    "botocore/data/cloudwatch",
    "botocore/data/codebuild",
    "botocore/data/codecommit",
    "botocore/data/codedeploy",
    "botocore/data/codeguru-reviewer",
    "botocore/data/codeguruprofiler",
    "botocore/data/codepipeline",
    "botocore/data/codestar",
    "botocore/data/codestar-connections",
    "botocore/data/codestar-notifications",
    "botocore/data/cognito-identity",
    "botocore/data/cognito-idp",
    "botocore/data/cognito-sync",
    "botocore/data/comprehend",
    "botocore/data/comprehendmedical",
    "botocore/data/compute-optimizer",
    "botocore/data/config",
    "botocore/data/connect",
    "botocore/data/connectparticipant",
    "botocore/data/cur",
    "botocore/data/dataexchange",
    "botocore/data/datapipeline",
    "botocore/data/datasync",
    "botocore/data/dax",
    "botocore/data/detective",
    "botocore/data/devicefarm",
    "botocore/data/directconnect",
    "botocore/data/discovery",
    "botocore/data/dlm",
    "botocore/data/dms",
    "botocore/data/docdb",
    "botocore/data/ds",
    "botocore/data/dynamodb",
    "botocore/data/dynamodbstreams",
    "botocore/data/ebs",
    "botocore/data/ec2",
    "botocore/data/ec2-instance-connect",
    "botocore/data/ecr",
    "botocore/data/ecs",
    "botocore/data/efs",
    "botocore/data/eks",
    "botocore/data/elastic-inference",
    "botocore/data/elasticache",
    "botocore/data/elasticbeanstalk",
    "botocore/data/elastictranscoder",
    "botocore/data/elb",
    "botocore/data/elbv2",
    "botocore/data/emr",
    "botocore/data/es",
    "botocore/data/events",
    "botocore/data/firehose",
    "botocore/data/fms",
    "botocore/data/forecast",
    "botocore/data/forecastquery",
    "botocore/data/frauddetector",
    "botocore/data/fsx",
    "botocore/data/gamelift",
    "botocore/data/glacier",
    "botocore/data/globalaccelerator",
    "botocore/data/glue",
    "botocore/data/greengrass",
    "botocore/data/groundstation",
    "botocore/data/guardduty",
    "botocore/data/health",
    "botocore/data/iam",
    "botocore/data/imagebuilder",
    "botocore/data/importexport",
    "botocore/data/inspector",
    "botocore/data/iot",
    "botocore/data/iot-data",
    "botocore/data/iot-jobs-data",
    "botocore/data/iot1click-devices",
    "botocore/data/iot1click-projects",
    "botocore/data/iotanalytics",
    "botocore/data/iotevents",
    "botocore/data/iotevents-data",
    "botocore/data/iotsecuretunneling",
    "botocore/data/iotthingsgraph",
    "botocore/data/kafka",
    "botocore/data/kendra",
    "botocore/data/kinesis",
    "botocore/data/kinesis-video-archived-media",
    "botocore/data/kinesis-video-media",
    "botocore/data/kinesis-video-signaling",
    "botocore/data/kinesisanalytics",
    "botocore/data/kinesisanalyticsv2",
    "botocore/data/kinesisvideo",
    "botocore/data/kms",
    "botocore/data/lakeformation",
    "botocore/data/lambda",
    "botocore/data/lex-models",
    "botocore/data/lex-runtime",
    "botocore/data/license-manager",
    "botocore/data/lightsail",
    "botocore/data/logs",
    "botocore/data/machinelearning",
    "botocore/data/macie",
    "botocore/data/managedblockchain",
    "botocore/data/marketplace-catalog",
    "botocore/data/marketplace-entitlement",
    "botocore/data/marketplacecommerceanalytics",
    "botocore/data/mediaconnect",
    "botocore/data/mediaconvert",
    "botocore/data/medialive",
    "botocore/data/mediapackage",
    "botocore/data/mediapackage-vod",
    "botocore/data/mediastore",
    "botocore/data/mediastore-data",
    "botocore/data/mediatailor",
    "botocore/data/meteringmarketplace",
    "botocore/data/mgh",
    "botocore/data/migrationhub-config",
    "botocore/data/mobile",
    "botocore/data/mq",
    "botocore/data/mturk",
    "botocore/data/neptune",
    "botocore/data/networkmanager",
    "botocore/data/opsworks",
    "botocore/data/opsworkscm",
    "botocore/data/organizations",
    "botocore/data/outposts",
    "botocore/data/personalize",
    "botocore/data/personalize-events",
    "botocore/data/personalize-runtime",
    "botocore/data/pi",
    "botocore/data/pinpoint",
    "botocore/data/pinpoint-email",
    "botocore/data/pinpoint-sms-voice",
    "botocore/data/polly",
    "botocore/data/pricing",
    "botocore/data/qldb",
    "botocore/data/qldb-session",
    "botocore/data/quicksight",
    "botocore/data/ram",
    "botocore/data/rds",
    "botocore/data/rds-data",
    "botocore/data/redshift",
    "botocore/data/rekognition",
    "botocore/data/resource-groups",
    "botocore/data/resourcegroupstaggingapi",
    "botocore/data/robomaker",
    "botocore/data/route53",
    "botocore/data/route53domains",
    "botocore/data/route53resolver",
    "botocore/data/s3control",
    "botocore/data/sagemaker",
    "botocore/data/sagemaker-a2i-runtime",
    "botocore/data/sagemaker-runtime",
    "botocore/data/savingsplans",
    "botocore/data/schemas",
    "botocore/data/sdb",
    "botocore/data/secretsmanager",
    "botocore/data/securityhub",
    "botocore/data/serverlessrepo",
    "botocore/data/service-quotas",
    "botocore/data/servicecatalog",
    "botocore/data/servicediscovery",
    "botocore/data/ses",
    "botocore/data/sesv2",
    "botocore/data/shield",
    "botocore/data/signer",
    "botocore/data/sms",
    "botocore/data/sms-voice",
    "botocore/data/snowball",
    "botocore/data/sns",
    "botocore/data/sqs",
    "botocore/data/ssm",
    "botocore/data/sso",
    "botocore/data/sso-oidc",
    "botocore/data/stepfunctions",
    "botocore/data/storagegateway",
    "botocore/data/sts",
    "botocore/data/support",
    "botocore/data/swf",
    "botocore/data/textract",
    "botocore/data/transcribe",
    "botocore/data/transfer",
    "botocore/data/translate",
    "botocore/data/waf",
    "botocore/data/waf-regional",
    "botocore/data/wafv2",
    "botocore/data/workdocs",
    "botocore/data/worklink",
    "botocore/data/workmail",
    "botocore/data/workmailmessageflow",
    "botocore/data/workspaces",
    "botocore/data/xray",
)


def find_useless_files(folder: Path) -> Generator[Path, None, None]:
    """Recursively yields files we want to remove."""
    for pattern in FILES:
        yield from folder.glob(pattern)


def main(args: List[str]) -> int:
    """
    Purge unneeded files from the packaged application.
    Take one or more folder arguments: "ndrive", "Nuxeo Drive.app".
    """
    for folder in args:
        print(f">>> [{folder}] Purging unneeded files")
        for file in find_useless_files(Path(folder)):
            if file.is_dir():
                shutil.rmtree(file)
            else:
                os.remove(file)
            print(f"[X] Removed {file}")
        print(f">>> [{folder}] Folder purged.")


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
