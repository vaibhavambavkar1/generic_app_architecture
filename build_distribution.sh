#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

echo "========================================================="
echo " Building Secured ERP Production Distribution Bundle"
echo "========================================================="

# Define version and output directory
VERSION=$(date +%Y%m%d)
DIST_DIR="dist/erp_release_$VERSION"
IMAGE_NAME="erp_framework_prod:latest"

echo "[1/5] Compiling and Obfuscating Docker Image..."
# Build the production image using the multi-stage Dockerfile to strip source code
docker build -f Dockerfile.prod -t $IMAGE_NAME .

echo "[2/5] Creating Distribution Workspace..."
mkdir -p $DIST_DIR

echo "[3/5] Exporting Docker Image to Tarball (This may take a minute)..."
# Save the compiled docker image into a portable tar file
docker save -o $DIST_DIR/erp_image.tar $IMAGE_NAME

echo "[4/5] Copying Necessary Deployment Files..."
# Provide the client with the docker-compose orchestrator and empty .env
cp docker-compose.prod.yml $DIST_DIR/docker-compose.yml
cp .env.example $DIST_DIR/.env.template
cp production_guidelines.md $DIST_DIR/DEPLOYMENT_GUIDE.md

# Create a small helper script for the client to load the image easily
cat << 'EOF' > $DIST_DIR/install.sh
#!/bin/bash
echo "Loading ERP Image into Docker..."
docker load -i erp_image.tar
echo "Image loaded! Please copy .env.template to .env, configure your secrets, and run 'docker compose up -d'"
EOF
chmod +x $DIST_DIR/install.sh

echo "[5/5] Packaging Final Release Bundle..."
# Compress the entire distribution folder into a single tar.gz archive
tar -czvf ${DIST_DIR}.tar.gz -C dist erp_release_$VERSION

# Clean up the uncompressed folder to save space
rm -rf $DIST_DIR

echo "========================================================="
echo "✅ Distribution Bundle Created Successfully!"
echo "📍 Location: ${DIST_DIR}.tar.gz"
echo ""
echo "You can now securely send '${DIST_DIR}.tar.gz' to your client."
echo "They do not need internet access to pull the image, they just run install.sh!"
echo "========================================================="
