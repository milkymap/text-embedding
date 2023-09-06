# text-semantic-embedding

# build image 

```bash
docker build -t text-embedding:gpu -f Dockerfile.gpu .
```

# run container 
```bash
    docker run --rm --name text-embedding -gpus all -v /path/to/transformers_cache/:/home/solver/transformers_cache -p 8000:8000 text-embedding:gpu --port 8000 --host '0.0.0.0' --model_name Sahajtomar/french_semantic --chunk_size 128 --nb_workers 2 --mounting_path "/"
```

