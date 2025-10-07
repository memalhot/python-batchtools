# echo "testing bj valid commands"
# python3 batchtools.py bj -h
# python3 batchtools.py bj --help
# # python3 batchtools.py bj -w
# # python3 batchtools.py bj --watch

# echo "testing bj invalid commands"
# python3 batchtools.py bj -z


# echo "testing bd valid commands"
# python3 batchtools.py bd -h
# python3 batchtools.py bd --help
# br nvidia-smi &
# sleep 3
# python3 batchtools.py bd
# #NEED TO ADD CASE FOR SPECIFIED WORKLOAD

# echo "testing bj invalid commands"
# python3 batchtools.py bd -z
# python3 batchtools.py bd thisisafakejob


# echo "testing bl valid commands"
# python3 batchtools.py bl -h
# python3 batchtools.py bl --help
# python3 batchtools.py bl
# python3 batchtools.py bl csw-dev-0
# br nvidia-smi
# python3 batchtools.py bl csw-dev-0 csw-dev-1

# echo "testing bl invalid commands"
# python3 batchtools.py bl -z
# python3 batchtools.py bl thisisafakepod

# echo "testing bq valid commands"
# python3 batchtools.py bq -h
# python3 batchtools.py bq --help
# python3 batchtools.py bq

# echo "testing bq invalid commands"
# python3 batchtools.py bq randomnewarg
# python3 batchtools.py bq -z


echo "testing valid bp commands"
python3 batchtools.py bp -h
python3 batchtools.py bp --help
br nvidia-smi &
sleep 3
python3 batchtools.py bp






