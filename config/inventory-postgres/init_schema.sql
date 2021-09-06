---------------------------------------------------------
----------------------- INVENTORY -----------------------
---------------------------------------------------------

-- CreateEnum
CREATE TYPE "Source" AS ENUM ('MANUAL', 'DISCOVERED', 'IMPORTED');

-- CreateEnum
CREATE TYPE "ServiceState" AS ENUM ('PLANNING', 'IN_SERVICE', 'OUT_OF_SERVICE');

-- CreateTable
CREATE TABLE "device_inventory" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "role" TEXT,
    "management_ip" TEXT,
    "config" JSONB,
    "model" TEXT,
    "software" TEXT,
    "sw_version" TEXT,
    "mac_address" TEXT,
    "serial_number" TEXT,
    "vendor" TEXT,
    "mount_parameters" JSONB,
    "username" TEXT,
    "password" TEXT,
    "tenant_id" TEXT NOT NULL,
    "uniconfig_zone" TEXT NOT NULL,
    "source" "Source" NOT NULL,
    "serviceState" "ServiceState" NOT NULL DEFAULT E'PLANNING',
    "location_id" TEXT,

    PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "uniconfig_zone" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "tenant_id" TEXT NOT NULL,

    PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "label" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "tenant_id" TEXT NOT NULL,

    PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "device_label" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "device_id" TEXT NOT NULL,
    "label_id" TEXT NOT NULL,

    PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "location" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "tenant_id" TEXT NOT NULL,
    "latitude" TEXT,
    "longitude" TEXT,
    "address_line_1" TEXT,
    "address_line_2" TEXT,
    "zip_code" TEXT,
    "sorting_code" TEXT,
    "dependent_locality" TEXT,
    "locality" TEXT,
    "administrative_area" TEXT,
    "country" TEXT NOT NULL,

    PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "device_blueprint" (
    "id" TEXT NOT NULL,
    "created_at" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updated_at" TIMESTAMP(3) NOT NULL,
    "name" TEXT NOT NULL,
    "tenant_id" TEXT NOT NULL,
    "template" TEXT NOT NULL,

    PRIMARY KEY ("id")
);

-- CreateIndex
CREATE UNIQUE INDEX "udx_device_name_tenant_id" ON "device_inventory"("name", "tenant_id");

-- CreateIndex
CREATE INDEX "idx_uniconfig_zone_tenant_id" ON "uniconfig_zone"("tenant_id");

-- CreateIndex
CREATE UNIQUE INDEX "udx_uniconfig_zone_name_tenant_id" ON "uniconfig_zone"("name", "tenant_id");

-- CreateIndex
CREATE UNIQUE INDEX "udx_label_name_tenant_id" ON "label"("name", "tenant_id");

-- CreateIndex
CREATE UNIQUE INDEX "udx_device_label_device_id_label_id" ON "device_label"("device_id", "label_id");

-- CreateIndex
CREATE UNIQUE INDEX "udx_location_name_tenant_id" ON "location"("name", "tenant_id");

-- CreateIndex
CREATE UNIQUE INDEX "udx_device_blueprint_name_tenant_id" ON "device_blueprint"("tenant_id", "name");

-- AddForeignKey
ALTER TABLE "device_inventory" ADD FOREIGN KEY ("uniconfig_zone") REFERENCES "uniconfig_zone"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "device_inventory" ADD FOREIGN KEY ("location_id") REFERENCES "location"("id") ON DELETE SET NULL ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "device_label" ADD FOREIGN KEY ("device_id") REFERENCES "device_inventory"("id") ON DELETE CASCADE ON UPDATE CASCADE;

-- AddForeignKey
ALTER TABLE "device_label" ADD FOREIGN KEY ("label_id") REFERENCES "label"("id") ON DELETE RESTRICT ON UPDATE CASCADE;
