variable "project_name" {
  description = "Nombre del proyecto o cliente (ej: 'acme-chat')"
  type        = string
}

variable "environment" {
  description = "Ambiente (dev, stg, prod)"
  type        = string
  default     = "dev"
}

variable "location" {
  description = "Región de Azure (ej: East US o Sweden Central para modelos nuevos)"
  type        = string
  default     = "East US"
}

variable "openai_model_name" {
  type    = string
  default = "gpt-4o"
}

variable "openai_model_version" {
  type    = string
  default = "2024-05-13"
}

variable "embedding_model_name" {
  description = "Nombre del modelo de embeddings"
  type        = string
  default     = "text-embedding-3-small"
}

variable "embedding_model_version" {
  type    = string
  default = "1"
}

variable "tokens_capacity" {
  description = "Tokens por minuto (en miles). Ej: 10 = 10k TPM"
  type        = number
  default     = 10
}