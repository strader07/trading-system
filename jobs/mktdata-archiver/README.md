# Daily Run

# Backfill

1. Generate FTX markets listed dates
```bash
cat ftx_markets_filter.txt | sed 's/|/,/g' | awk '{$1=$1};1' | sed 's/ , /,/g' > ftx_markets_filter.csv
```

2. Generate markets/dates jobs list
```python 
python list_jobs.py
```

3. Run:
```ruby
ruby generate_jobs.rb
```

- Add nodepool:
- Scale out tardis-machine
- Apply
- Run
