### Use sphinx-apidoc to auto-generate .rst files from your package:
```sh
cd docs
sphinx-apidoc -o source/ ../llmfy
```

### Build the Docs
```sh
cd docs
make html  
```

### Run the Docs
```sh
open build/html/index.html   
```
