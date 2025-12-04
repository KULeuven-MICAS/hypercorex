import matplotlib.pyplot as plt
import json
import numpy as np
import matplotlib.pyplot as plt


av_data = np.zeros([4, 9])

i = 0
while (i < 9):
    with open(f"hdc_exp/result_lang_{i}.json", "r") as f:
        result_dict = json.load(f)


    # Group data
    data = [[],[],[],[]]
    for key in result_dict.keys():
        if key[0:4] == '2048':
            if key[5:11] == 'binary':
                data[0].append(result_dict[key])
            else:
                data[1].append(result_dict[key])
        elif key[0:4] == '8192':
            if key[5:11] == 'binary':
                data[2].append(result_dict[key])
            else:
                data[3].append(result_dict[key])

    data = np.array(data)
    print(data)
    av_data = av_data + data
    i += 1

av_data = av_data / i

# Number of groups and bars per group
n_groups = 4
n_bars = 9

# Bar positions
bar_width = 0.1  # width of each bar
x = np.arange(n_groups)

# Create the plot
fig, ax = plt.subplots(figsize=(10, 6))

# Plot each of the 9 bars per group
for i in range(n_bars):
    ax.bar(x + i * bar_width, av_data[:, i], width=bar_width, label=f'Bar {i+1}')

# Labels and title
ax.set_ylabel('Prediction Accuracy')
ax.set_title('Language Recognition with Quantization')

# X-axis tick labels
ax.set_xticks(x + (n_bars/2 - 0.5) * bar_width)
ax.set_xticklabels(['D = 2048\nBinary', 'D = 2048\nBipolar', 'D = 8192\nBinary', 'D = 8192\nBipolar'])

# Add legend
legend = ['1-bit', 'INT8', 'INT4', 'INT2', 'FP8 E4M3', 'FP8_E5M2', 'FP6 E2M3', 'FP6 E3M2', 'FP4 E2M1']
ax.legend(legend, ncol=3, bbox_to_anchor=(1.05, 1), loc='upper left')

ax.set_ylim(0.85, 1.0)

plt.tight_layout()
plt.show()
plt.savefig("Barplot.png")
plt.savefig("Barplot.pdf")