MAIN = PageRank
JAR = ${MAIN}.jar

# local run settings
MASTER = local
PARALLELISM = 5
PERSIST = true
INPUT = wikipedia-simple-html.bz2
OUTPUT = output

# common remote run settings
BUCKET = s3://cheisler.cs6240.hw4
REGION = us-west-2
INSTANCE_TYPE = m4.large
AWS_MASTER = yarn-cluster
AWS_INPUT = ${BUCKET}/input
AWS_PERSIST = true

# 6 machine remote run settings
6_MACHINE_SUBNET = subnet-5ef07b06
6_MACHINE_PARALLELISM = 10
6_MACHINE_OUTPUT = output6
6_MACHINE_LOG = log6

# 11 machine remote run settings
11_MACHINE_SUBNET = subnet-62af9306
11_MACHINE_PARALLELISM = 20
11_MACHINE_OUTPUT = output11
11_MACHINE_LOG = log11

jar:
	sbt package
	cp target/scala*/pagerank_*.jar ${JAR}

run: jar
	rm -rf ${OUTPUT}
	sbt "run ${MASTER} ${PARALLELISM} ${PERSIST} ${INPUT} ${OUTPUT}"

upload: jar
	aws s3 cp ${JAR} ${BUCKET}

6machine: upload
	aws s3 rm ${BUCKET} --recursive --exclude "*" --include "${6_MACHINE_OUTPUT}*"
	aws s3 rm ${BUCKET} --recursive --exclude "*" --include "${6_MACHINE_LOG}*"	
	aws emr create-cluster \
		--name "6 Machines" \
		--release-label emr-5.0.3 \
		--instance-groups '[{"InstanceCount":5,"InstanceGroupType":"CORE","InstanceType":"${INSTANCE_TYPE}"},{"InstanceCount":1,"InstanceGroupType":"MASTER","InstanceType":"${INSTANCE_TYPE}"}]' \
		--applications Name=Hadoop Name=Spark \
		--steps '[{"Args":["spark-submit","--deploy-mode","cluster","--class","cs6240.${MAIN}","${BUCKET}/${JAR}","${AWS_MASTER}","${6_MACHINE_PARALLELISM}","${AWS_PERSIST}","${AWS_INPUT}","${BUCKET}/${6_MACHINE_OUTPUT}"],"Type":"CUSTOM_JAR","ActionOnFailure":"TERMINATE_CLUSTER","Jar":"command-runner.jar","Properties":"","Name":"${MAIN}"}]' \
		--log-uri ${BUCKET}/${6_MACHINE_LOG} \
		--service-role EMR_DefaultRole \
		--ec2-attributes InstanceProfile=EMR_EC2_DefaultRole,SubnetId=${6_MACHINE_SUBNET} \
		--region ${REGION} \
		--enable-debugging \
		--auto-terminate

11machine: upload
	aws s3 rm ${BUCKET} --recursive --exclude "*" --include "${11_MACHINE_OUTPUT}*"
	aws s3 rm ${BUCKET} --recursive --exclude "*" --include "${11_MACHINE_LOG}*"
	aws emr create-cluster \
		--name "11 Machines" \
		--release-label emr-5.0.3 \
		--instance-groups '[{"InstanceCount":10,"InstanceGroupType":"CORE","InstanceType":"${INSTANCE_TYPE}"},{"InstanceCount":1,"InstanceGroupType":"MASTER","InstanceType":"${INSTANCE_TYPE}"}]' \
		--applications Name=Hadoop Name=Spark \
		--steps '[{"Args":["spark-submit","--deploy-mode","cluster","--class","cs6240.${MAIN}","${BUCKET}/${JAR}","${AWS_MASTER}","${11_MACHINE_PARALLELISM}","${AWS_PERSIST}","${AWS_INPUT}","${BUCKET}/${11_MACHINE_OUTPUT}"],"Type":"CUSTOM_JAR","ActionOnFailure":"TERMINATE_CLUSTER","Jar":"command-runner.jar","Properties":"","Name":"${MAIN}"}]' \
		--log-uri ${BUCKET}/${11_MACHINE_LOG} \
		--service-role EMR_DefaultRole \
		--ec2-attributes InstanceProfile=EMR_EC2_DefaultRole,SubnetId=${11_MACHINE_SUBNET} \
		--region ${REGION} \
		--enable-debugging \
		--auto-terminate

clean:
	rm -rf ${JAR} ${OUTPUT} project target
