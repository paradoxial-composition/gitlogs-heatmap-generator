import os
import sys
import git
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
from collections import defaultdict
import time

def print_loading(message):
    print(f"\n{message}...", end="", flush=True)

def print_done():
    print(" Done!")

def get_git_logs(repo_path, author_name_or_email):
    repo = git.Repo(repo_path)
    logs = repo.git.log('--all', '--author={}'.format(author_name_or_email), '--pretty=format:%cd', '--date=short')
    return logs.splitlines()

def parse_dates(logs):
    dates = []
    today = datetime.today()
    ten_months_ago = today - timedelta(days=30 * 12)  # Approximation for 12 months
    
    for log in logs:
        date_str = log.split()[0]
        date = datetime.strptime(date_str, '%Y-%m-%d')
        
        # Include only commits from the past 12 months
        if date >= ten_months_ago:
            dates.append(date)
    
    return dates

def count_changes_by_weekday_month(dates):
    weekday_month_count = defaultdict(int)
    for date in dates:
        weekday = date.strftime('%A')  # Full weekday name (e.g., Monday)
        month = date.strftime('%B')    # Full month name (e.g., January)
        weekday_month_count[(weekday, month)] += 1
    return weekday_month_count

def create_heatmap_data(weekday_month_count):
    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    months = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    heatmap_data = pd.DataFrame(0, index=weekdays, columns=months)
    
    for (weekday, month), count in weekday_month_count.items():
        heatmap_data.at[weekday, month] += count
    
    return heatmap_data

def plot_heatmap(heatmap_data, title, output_file):
    plt.figure(figsize=(12, 6))
    plt.imshow(heatmap_data, cmap='YlOrBr', aspect='auto')
    
    plt.xticks(np.arange(len(heatmap_data.columns)), heatmap_data.columns, rotation=45)
    plt.yticks(np.arange(len(heatmap_data.index)), heatmap_data.index)
    
    plt.colorbar(label='Number of Changes')
    plt.title(title)
    plt.xlabel('Month')
    plt.ylabel('Day of the Week')
    
    plt.tight_layout()
    
    # Save the heatmap as an image file
    plt.savefig(output_file, dpi=300)
    plt.close()  # Close the plot to free memory

def main(repo_dir, author_name_or_email, output_dir="."):
    repo_count = 0
    global_weekday_month_count = defaultdict(int)  # Aggregate commit data across all repositories
    
    print_loading("Scanning repositories")
    for root, dirs, files in os.walk(repo_dir):
        if '.git' in dirs:
            repo_count += 1
            repo_path = root
            repo_name = os.path.basename(repo_path)
            
            print(f"\nProcessing repository: {repo_name}")
            
            # Get logs for the current repository
            logs = get_git_logs(repo_path, author_name_or_email)
            if not logs:
                print(f"No commits found for author: {author_name_or_email} in repository: {repo_name}")
                continue
            
            dates = parse_dates(logs)
            if not dates:
                print(f"No commits found in the past 12 months for author: {author_name_or_email} in repository: {repo_name}")
                continue
            
            print_loading("Processing commit dates")
            weekday_month_count = count_changes_by_weekday_month(dates)
            print_done()
            
            print_loading("Creating heatmap data")
            heatmap_data = create_heatmap_data(weekday_month_count)
            print_done()
            
            print_loading("Saving heatmap")
            plot_heatmap(heatmap_data, f'Git Changes in {repo_name} by {author_name_or_email}', 
                         os.path.join(output_dir, f"{repo_name}_heatmap.png"))
            print_done()
            
            # Aggregate commit data for the summary heatmap
            for (weekday, month), count in weekday_month_count.items():
                global_weekday_month_count[(weekday, month)] += count
            
            time.sleep(0.1)  # Simulate loading delay
    print_done()
    print(f"Processed {repo_count} repositories.")
    
    # Generate and save the summary heatmap
    if global_weekday_month_count:
        print_loading("Generating summary heatmap")
        summary_heatmap_data = create_heatmap_data(global_weekday_month_count)
        plot_heatmap(summary_heatmap_data, f'Summary of Git Changes Across All Repositories by {author_name_or_email}', 
                     os.path.join(output_dir, "summary_heatmap.png"))
        print_done()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python git_log_heatmap.py <repo_directory> <author_name_or_email>")
        sys.exit(1)
    
    repo_directory = sys.argv[1]
    author_name_or_email = sys.argv[2]
    
    # Ensure the output directory exists
    output_directory = os.path.dirname(os.path.abspath(__file__))  # Script's directory
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    print(f"Analyzing Git logs for author: {author_name_or_email}")
    main(repo_directory, author_name_or_email, output_directory)