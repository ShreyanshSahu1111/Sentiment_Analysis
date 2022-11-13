from folder_paths import sec_path, plot_path
from matplotlib import pyplot as plt
import pandas as pd


output_data=pd.read_excel(sec_path+"out4.xlsx")
columns=['positive_score',
        'negative_score',
        'polarity_score',
        'average_sentence_length',
        'percentage_of_complex_words',
        'fog_index',
        'complex_word_count',
        'word_count',
        'uncertainty_score',
        'constraining_score',
        'positive_word_proportion',
        'negative_word_proportion',
        'uncertainty_word_proportion',
        'constraining_word_proportion',
        'constraining_words_whole_report']

        
for column,i in zip(columns, range(1,len(columns)+1)):
    fig=plt.figure()
    plt.plot(output_data[column])
    plt.title(column+" of each report")
    plt.xlabel("serial no. of report")
    plt.ylabel(column)
    plt.savefig(plot_path+"%s_"%i+column+".png")
    plt.close()
