_site/index.html: $(wildcart *.yml) templates/index.html src/build.py venv
	. venv/bin/activate; python src/build.py > _site/index.html

venv: venv/touchfile

venv/touchfile: src/requirements.txt
	test -d venv || python -m venv venv
	. venv/bin/activate; pip install -Ur src/requirements.txt
	touch venv/touchfile

clean:
	rm -rf venv
