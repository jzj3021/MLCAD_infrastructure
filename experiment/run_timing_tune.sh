#/usr/bin/bash

DESIGN_DIR=/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/designs

cd ..
for DESIGN_FILE in $DESIGN_DIR/*; do
    DESIGN=$(basename $DESIGN_FILE)
    # if [[ $DESIGN == "ac97_top" || $DESIGN == "aes_cipher_top" || $DESIGN == "fpu" ]]; then
    #     continue
    # fi
    # for VAR in $(seq 0 -0.1 -0.5); do
        VAR=0
        # echo "Running timing tuning for design: $DESIGN, VAR: $VAR"
        # echo "openroad -python OpenROAD_timing_oriented.py \
        #     -design $DESIGN \
        #     -lef "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/platform/ASAP7/lef" \
        #     -lib "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/platform/ASAP7/lib" \
        #     -output "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/results" \
        #     -timing_tune $VAR"
        openroad -python OpenROAD_timing_oriented.py \
            -design $DESIGN \
            -lef "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/platform/ASAP7/lef" \
            -lib "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/platform/ASAP7/lib" \
            -output "/home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/results" \
            -timing_tune $VAR

        echo "openroad -python OpenROAD_flow.py \
            -d $DESIGN \
            -v /home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/results/${DESIGN}.v \
            -s /home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/experiment/results/${DESIGN}_timing_tune_${VAR}.score"
        openroad -python OpenROAD_flow.py \
            -d $DESIGN \
            -v /home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/results/${DESIGN}.v \
            -s /home/lancunqing/workspace/gitres/MLCAD25-Contest-Scripts-Benchmarks/src/evaluation/experiment/results/${DESIGN}_timing_tune_${VAR}.score
    done 
done