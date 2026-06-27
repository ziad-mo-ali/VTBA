import pandas as pd
from collections import Counter

projects = pd.read_csv("7-projects.tsv", sep="\t", index_col="id")["name"].to_dict()

counts = Counter()
for chunk in pd.read_csv("2-commits-diffs.tsv", sep="\t", chunksize=100_000, usecols=["projectId"]):
    counts.update(chunk["projectId"].value_counts().to_dict())

for project_id, count in sorted(counts.items()):
    name = projects.get(project_id, f"Unknown ({project_id})")
    print(f"{name}: {count}")