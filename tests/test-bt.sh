print_line() {
   sleep 1
   for (( i=0; i<50; i++ )); do
       printf '-'
   done
   printf '\n'
}

echo testing bq
batchtools bq
print_line

echo 'testing bps (verbose)'
batchtools --verbose bps
print_line

echo 'testing bps (not verbose)'
batchtools bps
print_line

echo 'testing br without gpu nowait'
batchtools br --gpu none --no-wait --name mtest ‘sleep 10 && echo test’
print_line

echo 'testing bd w/ one job, no args'
batchtools bd
print_line

echo 'testing br with gpu'
cat <<EOF > hello_test.cu
#include <stdio.h>


__global__ void
helloFromGPU(void)
{
   printf("Hello from GPU\\n");
}


int main(void)
{
   printf("Hello from CPU\\n");
   helloFromGPU <<< 1, 3 >>>();
   cudaDeviceSynchronize();
   cudaDeviceReset();
}
EOF

nvcc hello_test.cu -o hello

batchtools br './hello' | tee log.txt

print_line

echo 'testing batchtools br no command, should return error'
batchtools br

print_line

echo 'testing bp, bl, bd no specified jobs'
batchtools br --gpu none --no-wait 'sleep 10'

printf 'bp one job'
printf '\n'

batchtools bp
printf '\n'

printf 'bl one job'
printf '\n'

batchtools bl
printf '\n'

batchtools br --gpu none --no-wait 'sleep 10'

printf 'bp two jobs'
printf '\n'

batchtools bp
printf '\n'

printf 'bl two jobs'
printf '\n'

batchtools bl

printf 'bd two jobs, no args'
batchtools bd

print_line

echo 'testing br with context'

echo "Hello from CUDA file!" > input.txt

cat <<'EOF' > readfile.cu
#include <stdio.h>
#include <cuda_runtime.h>

__global__ void printFile(char *d) { printf("%s\n", d); }

int main() {
    FILE *f = fopen("input.txt", "r");
    char t[128]; fgets(t, 128, f); fclose(f);

    char *d; cudaMalloc(&d, 128);
    cudaMemcpy(d, t, 128, cudaMemcpyHostToDevice);
    printFile<<<1,1>>>(d);
    cudaDeviceSynchronize();
    cudaFree(d);
}
EOF

nvcc readfile.cu -o readfile

batchtools br './readfile'
print_line
