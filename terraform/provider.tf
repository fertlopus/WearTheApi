terraform {
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 3.11"
    }
  }

  backend "azurerm" {
    # TODO : Configure backends later when the infra is up and ready
  }
}

provider "azurerm" {
  features {}
}