echo "testing bj valid commands"
python3 batchtools.py bj -h
python3 batchtools.py bj --help
# python3 batchtools.py bj -w
# python3 batchtools.py bj --watch

echo "testing bj invalid commands"
python3 batchtools.py bj -z


echo "testing bd valid commands"
python3 batchtools.py bd -h
python3 batchtools.py bd --help
br nvidia-smi
python3 batchtools.py bd
#NEED TO ADD CASE FOR SPECIFIED WORKLOAD

echo "testing bj invalid commands"
python3 batchtools.py bd -z
python3 batchtools.py bd thisisafakejob


echo "testing bp valid commands"
python3 batchtools.py bp -h
python3 batchtools.py bp --help
python3 batchtools.py bp
python3 batchtools.py bp csw-dev-0
#NEED TO ADD CASE WITH MULTIPLE PODS

echo "testing bj invalid commands"
python3 batchtools.py bd -z
python3 batchtools.py bd thisisafakepod

echo "testing bq valid commands"
python3 batchtools.py bq -h
python3 batchtools.py bq --help
python3 batchtools.py bq

echo "testing bj invalid commands"
python3 batchtools.py bq randomnewarg
python3 batchtools.py bq -z







