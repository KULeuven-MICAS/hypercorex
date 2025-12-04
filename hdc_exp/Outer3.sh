conda activate hypercorex

for i in {1..5}; do
    echo "Run $i"
    python hdc_exp/Outer3.py "$i" &
done
disown