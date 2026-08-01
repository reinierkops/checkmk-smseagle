.PHONY: deploy manifest package clean

deploy:
	bash scripts/deploy.sh

manifest:
	bash scripts/build-manifest.sh

package:
	bash scripts/package.sh

clean:
	rm -rf build
	find . -name "__pycache__" -type d -exec rm -rf {} +
	find . -name "*.pyc" -delete
