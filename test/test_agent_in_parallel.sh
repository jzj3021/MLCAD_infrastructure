cd /app/MLCAD25-Contest-Scripts-Benchmarks/src/MLCAD_infrastructure/src/algorithm

# openroad -python agent.py --design_dir "/app/MLCAD25-Contest-Scripts-Benchmarks/designs/ac97_top"

# 创建一个数组存储所有子进程的退出状态
declare -a exit_codes
declare -a pids
# 移除引号，让shell正确展开通配符
for design_dir in /app/MLCAD25-Contest-Scripts-Benchmarks/designs/*; do
  # 确保目录存在且是目录
  (
  echo "Checking directory: $design_dir"
  if [ -d "$design_dir" ]; then
    design_name=$(basename "$design_dir")
    echo "Processing design: $design_name"
    
    # 运行10次迭代
    for i in $(seq 1 10); do
      echo "Running test $i for $design_name"
      # 传递确切的设计目录路径，而不是通配符模式
      openroad -python agent.py --design_dir "$design_dir"
      if [ $? -ne 0 ]; then
        echo "Test $i for $design_name failed"
        exit 1
      fi
    done
  fi
  ) &
  pids[$i]=$!
  echo "Started process $! for test $i"

done

echo "Waiting for all tests to complete..."
for pid in ${pids[@]}; do
  wait $pid
done

# 检查所有测试的退出状态
failed=0
for i in $(seq 1 10); do
  if [ -f "/tmp/test_${design_name}_${i}.exit" ]; then
    exit_code=$(cat "/tmp/test_${design_name}_${i}.exit")
    rm -f "/tmp/test_${design_name}_${i}.exit"
    
    if [ "$exit_code" -ne 0 ]; then
      echo "Test $i failed with exit code $exit_code"
      failed=1
    fi
  else
    echo "Warning: No exit code file found for test $i"
  fi
done

# 如果有任何测试失败，则退出
if [ $failed -ne 0 ]; then
  echo "One or more tests failed for $design_name"
  exit 1
fi

exit 0