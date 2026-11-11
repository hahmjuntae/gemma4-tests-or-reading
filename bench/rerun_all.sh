#!/bin/bash
# API 한도로 끊긴 실행만 과제 하나씩, 건당 25분 제한으로 다시 돌림
cd "$(dirname "$0")/.."
export GEMINI_API_KEY=$(security find-generic-password -s hackathon-gemini-kic -w)
for tag in gemma-4-26b-a4b-it__blind gemma-4-26b-a4b-it__tests gemma-4-31b-it__blind gemma-4-31b-it__tests; do
  m=${tag%%__*}; c=${tag##*__}
  ids=$(.venv/bin/python bench/rerun_crashed.py $tag)
  for id in ${ids//,/ }; do
    echo "$(date +%H:%M) start $tag $id"
    timeout 1500 .venv/bin/python bench/run.py --model gemini/$m --cond $c --only $id --steps 12 --workers 1 --tasks-file bench/batch1.json
    echo "$(date +%H:%M) end $tag $id rc=$?"
    sleep 20
  done
done
echo ALLDONE
