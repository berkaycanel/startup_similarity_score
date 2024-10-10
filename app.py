import streamlit as st
import pandas as pd
import ast

def safe_literal_eval(val):
    try:
        if pd.isna(val):
            return val
        return ast.literal_eval(val)
    except (ValueError, SyntaxError):
        return val


def calculate_similarity_score(domain, df):
    domain_row = df[df['domain'] == domain].iloc[0]
    similarity_scores = []
    for idx, row in df.iterrows():
        if row['domain'] == domain:
            continue  
        
        total_score = 0
        matching_parts = {"Employees": "", "Funding stage": "", "Combined_Tags": ""}

        if row['Employees'] == domain_row['Employees']:
            total_score += 0.20
            matching_parts["Employees"] = row["Employees"]

        # 2. Compare Funding stage column (20% contribution)
        # If Funding stage is "Unbekannt", give 0% contribution and don't append to matching parts
        if domain_row['Funding stage'] != "Unbekannt" and row['Funding stage'] != "Unbekannt":
            if row['Funding stage'] == domain_row['Funding stage']:
                total_score += 0.20
                matching_parts["Funding stage"] = row["Funding stage"]

        # 3. Compare refined_gpt_tags (60% contribution based on word match)
        domain_tags = domain_row['Combined_Tags'] if isinstance(domain_row['Combined_Tags'], list) else []
        row_tags = row['Combined_Tags'] if isinstance(row['Combined_Tags'], list) else []

        common_tags = set(domain_tags).intersection(set(row_tags))
        common_tag_count = len(common_tags)

        if common_tag_count > 0:
            total_score += min(0.12 * common_tag_count, 0.60)  # Scale up to 5 matches for 60%
            matching_parts["Combined_Tags"] = ", ".join(common_tags)
        
        # Append the domain, its similarity score, and matching parts to the list
        similarity_scores.append((row['domain'], total_score, matching_parts))
    
    # Sort the domains by similarity score in descending order and return the top 10
    similarity_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Format the result as a list of dictionaries for table display
    result_table = []
    for domain, score, matches in similarity_scores[:10]:
        row_dict = {"Domain": domain, "Score": f"{score:.2f}"}
        row_dict.update(matches)
        row_dict['Matched Keywords'] = row_dict['Combined_Tags']
        del row_dict['Combined_Tags']
        result_table.append(row_dict)

    
    
    return result_table, domain_row




# Streamlit app with improved layout and input box
def main():
    st.title("🔍 Domain Similarity Checker")
    st.write("Enter a domain to find the most similar domains based on employees, funding stage, and key tags.")

    # Fixed DataFrame (replace this with your real data)
    df = pd.read_csv('similarity_df_plus_WP_tags.csv')
    # Domain input box
    df['Combined_Tags'] = df['Combined_Tags'].apply(safe_literal_eval)

    domain = st.text_input("🔗 Enter domain (e.g., 'n26.com')", '')

    if st.button("Find Similar Domains"):
        if domain in df['domain'].values:
            result_table, domain_row = calculate_similarity_score(domain, df)
            st.subheader("Input Domain Details")
            input_domain_details = pd.DataFrame([{
                "Domain": domain_row['domain'],
                "Employees": domain_row['Employees'],
                "Funding stage": domain_row['Funding stage'],
                "Combined_Tags": ", ".join(domain_row['Combined_Tags']) if isinstance(domain_row['Combined_Tags'], list) else ""
            }])
            st.table(input_domain_details)
            
            # Display the similarity table
            st.subheader("Top 10 Similar Domains")
            if result_table:
                st.table(pd.DataFrame(result_table))
            else:
                st.write("No similar domains found.")
        else:
            st.error("Domain not found in the dataset! Please try another domain.")
            
if __name__ == "__main__":
    main()
