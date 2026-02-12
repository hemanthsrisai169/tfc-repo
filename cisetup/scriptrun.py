"""
Description : This script would fetch the latest build and config version and triggers the Deployment Job with Build Id and Config as parameter

Input :
Secrets is passed as input which has been added in rio project settings
'release' variable needs to be changed to make it work for every release and to be merged into specific release branch and develop branch.

Output: rundeploy.sh will be triggered with latest build id and config version
"""

import os
import sys
import urllib.request
import json
import re
import cx_Oracle
import ssl

secret = str(sys.argv[1])
dbusername = str(sys.argv[2])
emailid = str(sys.argv[3])
projectid = str(sys.argv[4])
release_version_db = ""
release = ""
release_conf = ""
latest_buildid = ""
deploy_job = ""

try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    # Legacy Python that doesn't verify HTTPS certificates by default
    pass
else:
    # Handle target environment that doesn't support HTTPS verification
    ssl._create_default_https_context = _create_unverified_https_context

##Connect DB and Read Release and Config versions
try:
    connstr = cx_Oracle.makedsn('ms11q01ad-oracle005.iad.apple.com', '1526', service_name='msmd01q4')
    con = cx_Oracle.connect(user=dbusername, password=dbusername, dsn=connstr)
    cursor = con.cursor()
    sql1 = "Select release_version from iad_cisetup where rio_projectid='" + projectid + "'"
    sql2 = "Select release_version, config_version, deploy_job from iad_cirun where rio_projectid='" + projectid + "'"
    cursor.execute(sql1)
    result = cursor.fetchone()
    release_version_db = result[0]
    cursor.execute(sql2)
    result = cursor.fetchone()
    release = result[0]
    release_conf = result[1]
    deploy_job = result[2]
    if not release_conf:
        release_conf = release
    branch = "release" + "-" + release
    pipeline_spec_url = "https://rio-api.pie.apple.com/v1/projects/" + projectid + "/pipeline_specs/" + projectid + "-" + branch + "-publish"
    print("pipelinespec url is --" + pipeline_spec_url)

except cx_Oracle.DatabaseError as e:
    print("There is a problem with Oracle", e)
    exit()

finally:
    if cursor:
        cursor.close()
    if con:
        con.close()

##Run if version is insynch
if (str(release) != str(release_version_db)):
    print("Since the version--" + release + " to run is not synch with--" + release_version_db + " exiting test")
    exit()

##Getting latest pipeline id###
request = urllib.request.Request(pipeline_spec_url)
request.add_header('Cache-Control', 'no-cache')
request.add_header('X-RIO-API-EMAIL', emailid)
request.add_header('Content-Type', 'application/json')
request.add_header('X-RIO-API-TOKEN', secret)
response = urllib.request.urlopen(request)
json_data = str(response.read().decode('utf-8').replace('\0', ''))
loaded_json = json.loads(json_data)
latest_pipeline_id = loaded_json["last_pipeline_id"]
facts_api_endpoint = "https://rio-api.pie.apple.com/v1/pipelines/" + latest_pipeline_id + "/facts"
print(facts_api_endpoint)

##Invoke facts api respone##
request_facts = urllib.request.Request(facts_api_endpoint)
request_facts.add_header('Cache-Control', 'no-cache')
request_facts.add_header('X-RIO-API-EMAIL', emailid)
request_facts.add_header('Content-Type', 'application/json')
request_facts.add_header('X-RIO-API-TOKEN', secret)
response_facts = urllib.request.urlopen(request_facts)
json_data_facts = str(response_facts.read().decode('utf-8').replace('\0', ''))
loaded_json_facts = json.loads(json_data_facts)
for data in loaded_json_facts:
    if ('artifacts' in data):
        loaded_json_facts2 = data
        break

artifacts = loaded_json_facts2["artifacts"]["docker"][0]["uri"]
buildid = str(artifacts.split(":", -1)[1])
if re.search("^[0-9]", buildid) != None:
    print("The latest buildid is--" + buildid)
else:
    artifacts = loaded_json_facts2["artifacts"]["docker"][1]["uri"]
    buildid = str(artifacts.split(":", -1)[1])
    print("The latest buildid is--" + buildid)

##Get latest Conf Version##
projectid_conf = "ap-adplatforms-display-cs-config"
branch_conf = release_conf + "-" + "publish"
pipeline_spec_url_conf = "https://rio-api.pie.apple.com/v1/projects/" + projectid_conf + "/pipeline_specs/" + projectid_conf + "-" + branch_conf
request_conf = urllib.request.Request(pipeline_spec_url_conf)
request_conf.add_header('Cache-Control', 'no-cache')
request_conf.add_header('X-RIO-API-EMAIL', emailid)
request_conf.add_header('Content-Type', 'application/json')
request_conf.add_header('X-RIO-API-TOKEN', secret)
response_conf = urllib.request.urlopen(request_conf)
json_data_conf = str(response_conf.read().decode('utf-8').replace('\0', ''))
loaded_json_conf = json.loads(json_data_conf)
latest_pipeline_id_conf = loaded_json_conf["last_pipeline_id"]
facts_api_endpoint_conf = "https://rio-api.pie.apple.com/v1/pipelines/" + latest_pipeline_id_conf + "/facts"

##Invoke facts api respone##
request_facts_conf = urllib.request.Request(facts_api_endpoint_conf)
request_facts_conf.add_header('Cache-Control', 'no-cache')
request_facts_conf.add_header('X-RIO-API-EMAIL', emailid)
request_facts_conf.add_header('Content-Type', 'application/json')
request_facts_conf.add_header('X-RIO-API-TOKEN', secret)
response_facts_conf = urllib.request.urlopen(request_facts_conf)
json_data_facts_conf = str(response_facts_conf.read().decode('utf-8').replace('\0', ''))
loaded_json_facts_conf = json.loads(json_data_facts_conf)
for data in loaded_json_facts_conf:
    if 'payload' in data and 'rioBuildNumber' in (str(data["payload"])):
        response_parsed_conf = data
        break
conf_build_number = str(response_parsed_conf["payload"]["rioBuildNumber"])
conf_version = release_conf + "-" + conf_build_number
print("The latest conf version--" + conf_version)

cmd_execute = "os.system(\"sh ./cisetup/rundeploybuild.sh" + " " + secret + " " + buildid + " " + conf_version +" "+ release_conf + " " + emailid + " " + projectid + " "+ deploy_job+ "\")"
eval(cmd_execute)