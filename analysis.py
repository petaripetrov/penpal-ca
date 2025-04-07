import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import os
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import re

# Set path (update as needed)
path = "data"

word_recall_results = []
engagement_results = []

# DATA PROCESSING
def replace_missing_rows(memory_df, no_memory_df):
    # replace with the column average

    memory_ids = set(memory_df['ID'])
    no_memory_ids = set(no_memory_df['ID'])

    # Find unmatched IDs
    only_in_memory = memory_ids - no_memory_ids
    only_in_no_memory = no_memory_ids - memory_ids

    # Fill in missing no_memory rows
    for pid in only_in_memory:
        avg_score = no_memory_df['Score'].mean()
        fake_row = pd.DataFrame([{
            'ID': pid,
            'Score': avg_score,
            'Memory': 0
        }])
        no_memory_df = pd.concat([no_memory_df, fake_row], ignore_index=True)

    # Fill in missing memory rows
    for pid in only_in_no_memory:
        avg_score = memory_df['Score'].mean()
        fake_row = pd.DataFrame([{
            'ID': pid,
            'Score': avg_score,
            'Memory': 1
        }])
        memory_df = pd.concat([memory_df, fake_row], ignore_index=True)

    return memory_df, no_memory_df

def remove_missing_rows(memory_df,no_memory_df):
    common_ids = set(memory_df['ID']).intersection(
        no_memory_df['ID']
    )

    memory_df = memory_df[memory_df['ID'].isin(common_ids)]
    no_memory_df = no_memory_df[no_memory_df['ID'].isin(common_ids)]

    return memory_df, no_memory_df

def count_languages(text):
    if not isinstance(text, str):
        return 0  # Handle non-string values gracefully
    
    # Clean the text by removing unnecessary words and phrases
    cleaned_text = re.sub(r'\b(native|a bit of|a bit|is my native langauge|is my|is|and some|and|language)\b', '', text, flags=re.IGNORECASE)
    
    # Replace hyphens with spaces to avoid splitting valid language names
    cleaned_text = cleaned_text.replace('-', ' ')
    
    # Split the text into individual languages using commas, spaces, or other delimiters
    languages = [lang.strip() for lang in re.split(r'[,\s]+', cleaned_text) if lang.strip()]
    
    # Return the count of unique languages
    return len(languages)

# LOAD DATA
def load_data(language):
    memory_df = pd.read_csv(os.path.join(path, f"Memory-{language}.csv"))
    no_memory_df = pd.read_csv(os.path.join(path, f"No-memory-{language}.csv"))
    
    memory_df['Memory'] = 1 # Assign 1 for memory 
    no_memory_df['Memory'] = 0 # Assign 0 for no memory

    memory_df.columns = memory_df.columns.str.strip()
    no_memory_df.columns = no_memory_df.columns.str.strip()

    # Drop any column that is entirely empty
    memory_df.dropna(axis=1, how='all', inplace=True)
    no_memory_df.dropna(axis=1, how='all', inplace=True)
    
    memory_df = memory_df[['Please enter your participant ID', 'Score', 'Memory']].rename(columns={"Please enter your participant ID": "ID"})
    no_memory_df = no_memory_df[['Please enter your participant ID', 'Score', 'Memory']].rename(columns={"Please enter your participant ID": "ID"})

    # Replace missing rows with average scores
    memory_df, no_memory_df = replace_missing_rows(memory_df, no_memory_df)

    return pd.concat([memory_df, no_memory_df])

def load_data_all_languages(languages):
    all_data = []
    for lang in languages:
        # load_data now already replaces missing rows with average scores
        data = load_data(lang)
        data['Language'] = lang  # add a column for language
        data = data.rename(columns={"Please enter your participant ID": "ID"})
        all_data.append(data)
    return pd.concat(all_data, ignore_index=True)

def load_engagement_data():
    engagement_df = pd.read_csv(os.path.join(path, "Survey.csv"))

    engagement_df = engagement_df.rename(columns={
        'Please enter your participant ID': 'ID',
    })

    # If any cell is empty, drop the entire row
    engagement_df.dropna(how='any', inplace=True)
    
    engagement_columns = engagement_df.columns[5:17]
    for col in engagement_columns:
        engagement_df[col] = engagement_df[col].apply(convert_likert_response)

    memory_df = engagement_df[engagement_df['Memory'] == 'Yes']
    no_memory_df = engagement_df[engagement_df['Memory'] == 'No']

    # map memory condition to 1 and no memory condition to 0
    memory_df = memory_df.copy()
    no_memory_df = no_memory_df.copy()

    memory_df['Memory'] = memory_df['Memory'].str.strip().str.capitalize().map({'Yes': 1, 'No': 0})
    no_memory_df['Memory'] = no_memory_df['Memory'].str.strip().str.capitalize().map({'Yes': 1, 'No': 0})
    
    return memory_df, no_memory_df

# PLOTTING
def plot_word_recall_scores(language):
    memory_df = pd.read_csv(os.path.join(path, f"Memory-{language}.csv"))
    no_memory_df = pd.read_csv(os.path.join(path, f"No-memory-{language}.csv"))

    memory_df['Memory'] = 1
    no_memory_df['Memory'] = 0

    memory_df.columns = memory_df.columns.str.strip()
    no_memory_df.columns = no_memory_df.columns.str.strip()

    memory_df['Score'] = pd.to_numeric(memory_df['Score'], errors='coerce')
    no_memory_df['Score'] = pd.to_numeric(no_memory_df['Score'], errors='coerce')

    # rename ID column
    memory_df = memory_df.rename(columns={"Please enter your participant ID": "ID"})
    no_memory_df = no_memory_df.rename(columns={"Please enter your participant ID": "ID"})

    df = pd.concat([memory_df[['ID', 'Score', 'Memory']],
                    no_memory_df[['ID', 'Score', 'Memory']]])

    os.makedirs("plots/recall", exist_ok=True)

    # Distribution Plot
    plt.figure(figsize=(8, 5))
    sns.histplot(data=df, x='Score', hue='Memory', kde=True, palette='pastel', element='step')
    plt.title(f"{language} - Score Distribution")
    plt.savefig(f"plots/recall/{language}_score_distribution.png")
    plt.close()

def plot_engagement_category_distributions(merged_df, categories):
    # Prepare the data for plotting
    long_data = []
    for category, questions in categories.items():
        df_category = merged_df[['ID', 'Memory'] + [category]].copy()
        df_category = df_category.rename(columns={category: 'Score'})
        df_category['Category'] = category
        long_data.append(df_category)

    # Combine all categories into a single DataFrame
    combined_long = pd.concat(long_data, ignore_index=True)

    # Ensure the Score column is numeric
    combined_long['Score'] = pd.to_numeric(combined_long['Score'], errors='coerce')

    # Map category labels to more descriptive names
    category_labels = {
        'FA': 'Focused Attention (FA)',
        'PU': 'Perceived Usability (PU)',
        'AE': 'Aesthetic Elements (AE)',
        'RW': 'Reward Factor (RW)'
    }
    combined_long['Category'] = combined_long['Category'].map(category_labels)
    combined_long['Memory'] = pd.Categorical(combined_long['Memory'], categories=[1, 0], ordered=True)
    
    # Plot the violin plot
    os.makedirs("plots/engagement", exist_ok=True)
    plt.figure(figsize=(12, 6))
    sns.violinplot(
        data=combined_long,
        x='Category',
        y='Score',
        hue='Memory',
        split=True,
        palette="pastel" 
    )
    plt.title("Distribution of Engagement Scores by User Engagement Category")
    plt.xlabel("Category")
    plt.ylabel("Score")
    plt.legend(title="Memory Condition", loc="upper right")
    plt.tight_layout()
    plt.savefig("plots/engagement/category_violin_plot.png")
    plt.close()

# WORD RETENTION TEST ANALYSIS
def test_word_recall(language, data):
    # Align data by ID
    data['Memory'] = data['Memory'].astype(int)

    paired_data = data.pivot(index='ID', columns='Memory', values='Score').dropna()
    memory = pd.to_numeric(paired_data[1], errors='coerce')
    no_memory = pd.to_numeric(paired_data[0], errors='coerce')

    print(paired_data.columns)

    # test for normality
    if stats.shapiro(no_memory)[1] > 0.05 and stats.shapiro(memory)[1] > 0.05:
        t_stat, p_value = stats.ttest_rel(memory, no_memory)
        test_used = "Paired t-test"
    else:
        t_stat, p_value = stats.wilcoxon(memory, no_memory)
        test_used = "Wilcoxon signed-rank test"

    print(f"{language}: {test_used}: Statistic={t_stat}, p-value={p_value}")
    word_recall_results.append({
        'Language': language,
        'Test': test_used,
        'Statistic': t_stat,
        'p-value': p_value
    })

def word_recall_individual_analysis():
    languages = ["Spanish", "French", "Japanese", "German"]
    for lang in languages:
        data = load_data(lang)
        test_word_recall(lang, data)
        plot_word_recall_scores(lang)

# def measure_word_recall_all_languages():
#     languages = ["Spanish", "French", "Japanese", "German"]
#     all_data = load_data_all_languages(languages)

#     # save all data to CSV
#     all_data.to_csv("output/recall_all_languages.csv", index=False)

#     all_data['Score'] = pd.to_numeric(all_data['Score'], errors='coerce')
#     all_data.dropna(subset=['Score'], inplace=True)

#     print(all_data['Score'].describe())

#     # Fit the mixed-effects model:
#     # Score ~ condition is our fixed effect
#     # groups=Language tells the model to use language as a random intercept
#     model = smf.mixedlm("Score ~ C(Memory)", data=all_data, groups=all_data["Language"])
#     model_fit = model.fit()

#     print(model_fit.summary())

#     # save the model summary to a CSV file
#     with open("output/recall_mixed_effects_model_summary.txt", "w") as f:
#         f.write(str(model_fit.summary()))

#     sns.violinplot(data=all_data, x="Language", y="Score", hue="Memory", split=True, palette="pastel")
#     plt.title("Distribution of Word Recall Scores by Language and Memory Condition")
#     plt.savefig("plots/recall/recall_violin_plot.png")
#     plt.show()
#     plt.close()

def measure_word_recall_all_languages():
    import scipy.stats as stats
    languages = ["Spanish", "French", "Japanese", "German"]
    all_data = load_data_all_languages(languages)

    # Save all combined data
    os.makedirs("output", exist_ok=True)
    all_data.to_csv("output/recall_all_languages.csv", index=False)

    all_data['Score'] = pd.to_numeric(all_data['Score'], errors='coerce')
    all_data.dropna(subset=['Score'], inplace=True)

    # print(all_data['Score'].describe())

    # Mixed-effects model (overall effect of memory)
    model = smf.mixedlm("Score ~ C(Memory)", data=all_data, groups=all_data["Language"])
    model_fit = model.fit()
    print(model_fit.summary())

    with open("output/recall_mixed_effects_model_summary.txt", "w") as f:
        f.write(str(model_fit.summary()))

    # Language-wise comparison results
    results = []
    for lang in languages:
        subset = all_data[all_data["Language"] == lang]
        pivoted = subset.pivot(index="ID", columns="Memory", values="Score").dropna()
        if pivoted.shape[0] < 2:
            continue  # Skip if not enough data

        memory_scores = pivoted[1]
        no_memory_scores = pivoted[0]

        # Choose parametric or non-parametric based on normality
        if stats.shapiro(memory_scores)[1] > 0.05 and stats.shapiro(no_memory_scores)[1] > 0.05:
            stat, p = stats.ttest_rel(memory_scores, no_memory_scores)
            test = "Paired t-test"
        else:
            stat, p = stats.wilcoxon(memory_scores, no_memory_scores)
            test = "Wilcoxon signed-rank test"

        mean_diff = memory_scores.mean() - no_memory_scores.mean()

        results.append({
            "Language": lang,
            "Test": test,
            "Mean_Difference": mean_diff,
            "Statistic": stat,
            "p-value": p
        })

    # Save per-language test results
    results_df = pd.DataFrame(results)
    results_df.to_csv("output/recall_per_language_stats.csv", index=False)
    print(results_df)

    # Plot
    os.makedirs("plots/recall", exist_ok=True)
    sns.violinplot(data=all_data, x="Language", y="Score", hue="Memory", split=True, palette="pastel")
    plt.title("Distribution of Word Recall Scores by Language and Memory Condition")
    plt.savefig("plots/recall/recall_violin_plot.png")
    plt.show()
    plt.close()


# PARTICIPANT BACKGROUND EFFECTS ON WORD RECALL
def analyze_background_effects_on_word_recall():
    # 1. Load the survey data
    survey_df = pd.read_csv(os.path.join(path, "Survey.csv"))
    
    survey_df.columns = survey_df.columns.str.strip()

    survey_info = survey_df[[
        'Please enter your participant ID',
        'What languages are you familiar with?',
        'Do you have experience with language learning?',
        'Have you used conversational assistants or language-learning chatbots?'
    ]].copy()

    # Clean column names
    survey_info.columns = ['ID', 'NumLanguages', 'PriorExperience', 'CAFamiliarity']

    survey_info['PriorExperience'] = survey_info['PriorExperience'].map({'Yes': 1, 'No': 0})
    survey_info['CAFamiliarity'] = survey_info['CAFamiliarity'].map({'Yes': 1, 'No': 0})
    # convert the strings of languages into a count using regex function above
    survey_info['NumLanguages'] = survey_info['NumLanguages'].apply(count_languages)

    # drop duplicates as participants filled in this part twice but entries didnt change
    survey_info = survey_info.drop_duplicates(subset=['ID'])

    # load the word recall data
    word_recall_data = load_data_all_languages(["Spanish", "French", "Japanese", "German"])
    
    # merge the two dataframes on 'ID'
    merged = pd.merge(word_recall_data, survey_info, on='ID')

    # fit mixed-effects model
    model = smf.mixedlm(
        "Score ~ Memory * NumLanguages + PriorExperience + CAFamiliarity",  # Confounding variables
        data=merged,
        groups=merged["ID"],  # Random effect for repeated measures
    )
    result = model.fit()
    print(result.summary())

    # save the model summary to a CSV file
    with open("output/recall_background_effects_summary.txt", "w") as f:
        f.write(str(result.summary()))

# ENGAGEMENT SURVEY ANALYSIS
def compute_composite_scores(df, min_col, max_col, new_col_name):
    # Ensure the selected columns are numeric
    numeric_columns = df.iloc[:, min_col:max_col].apply(pd.to_numeric, errors='coerce')
    
    # Fill missing values with column mean
    numeric_columns.fillna(numeric_columns.mean(), inplace=True)
    
    # Calculate the mean score for the given set of questions
    df[new_col_name] = numeric_columns.mean(axis=1)
    return df

def convert_likert_response(response):
    mapping = {
        "Strongly Disagree": 1,
        "Disagree": 2,
        "Neither agree nor disagree": 3,
        "Agree": 4,
        "Strongly agree": 5
    }
    return mapping.get(response, None)

def merge_engagement_data(memory_df, no_memory_df, engagement_columns):
    # Extract columns [5:17] and rename them to engagement_columns
    memory_df = memory_df.iloc[:, [1] + [-1] + list(range(5, 17))].copy()  # Include ID column
    no_memory_df = no_memory_df.iloc[:, [1] + [-1] + list(range(5, 17))].copy()  # Include ID column
        
    memory_df.columns = ['ID'] + ['Memory'] +  engagement_columns
    no_memory_df.columns = ['ID'] + ['Memory'] + engagement_columns

    # Merge the two DataFrames
    merged_df = pd.concat([memory_df, no_memory_df], ignore_index=True)

    return merged_df

def test_category_effect(engagement_df, category):
     # Separate the data by memory condition
    memory = engagement_df[engagement_df['Memory'] == 1][category].dropna()
    no_memory = engagement_df[engagement_df['Memory'] == 0][category].dropna()

    stat, p_value = stats.wilcoxon(memory, no_memory)

    print(f"{category}: Wilcoxon signed-rank test: Statistic={stat}, p-value={p_value}")

    # Append the results to engagement_results
    engagement_results.append({
        'Category': category,
        'Test': 'Wilcoxon signed-rank test',
        'Statistic': stat,
        'p-value': p_value
    })

def test_user_engagement():
    # Map questions to categories
    categories = {
        'FA': ['FA_Q1', 'FA_Q2', 'FA_Q3'],
        'PU': ['PU_Q1', 'PU_Q2', 'PU_Q3'],
        'AE': ['AE_Q1', 'AE_Q2', 'AE_Q3'],
        'RW': ['RW_Q1', 'RW_Q2', 'RW_Q3']
    }

    # Flatten all category questions into engagement_columns
    engagement_columns = [q for questions in categories.values() for q in questions]

    # Load and merge engagement data
    memory_df, no_memory_df = load_engagement_data()
    merged = merge_engagement_data(memory_df, no_memory_df, engagement_columns)


    # Calculate composite scores for each category
    start_col = 2  # Start index for the first category
    for i, (category, questions) in enumerate(categories.items()):
        merged = compute_composite_scores(merged, start_col, start_col + len(questions), category)
        start_col += len(questions)

    # Print merged DataFrame info
    print(merged.columns)
    print(merged.shape)

    # Test the effect of memory condition on each category
    for category in categories.keys():
        test_category_effect(merged, category)

    # Plot the engagement scores
    plot_engagement_category_distributions(merged, categories)

#begums version
def test_word_recall2(language, data):
    paired_data = data.pivot(index='ID', columns='Memory', values='Score').dropna()
    memory = pd.to_numeric(paired_data[1], errors='coerce')
    no_memory = pd.to_numeric(paired_data[0], errors='coerce')
    
    if stats.shapiro(no_memory)[1] > 0.05 and stats.shapiro(memory)[1] > 0.05:
        t_stat, p_value = stats.ttest_rel(no_memory, memory)
        test_used = "Paired t-test"
    else:
        t_stat, p_value = stats.wilcoxon(no_memory, memory)
        test_used = "Wilcoxon signed-rank test"
    
    print(f"{language}: {test_used}: Statistic={t_stat}, p-value={p_value}")
    word_recall_results.append({
        'Language': language,
        'Test': test_used,
        'Statistic': t_stat,
        'p-value': p_value
    })

if __name__ == "__main__":
    # 1. Word Recall Analysis
    # word_recall_individual_analysis()
    # pd.DataFrame(word_recall_results).to_csv("output/word_recall_results.csv", index=False)

    measure_word_recall_all_languages()

    analyze_background_effects_on_word_recall()

    # 2. User Engagement Analysis
    test_user_engagement()
    pd.DataFrame(engagement_results).to_csv("output/engagement_results.csv", index=False)



