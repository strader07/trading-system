variable "general" {
  type        = map(string)
  description = "Global parameters"
}

variable "cluster" {
  type        = map(string)
  description = "Kubernetes cluster parameters to initialize"
}

variable "node_pool" {
  type        = list(map(any))
  default     = []
  description = "Node pool setting to create"
}

variable "node_pool_taint" {
  type        = list(map(any))
  default     = []
  description = "Tainted node pool setting to create"
}

variable "tags" {
  type        = list(string)
  default     = []
  description = "The list of instance tags applied to all nodes. Tags are used to identify valid sources or targets for network firewalls"
}

variable "labels" {
  description = "The Kubernetes labels (key/value pairs) to be applied to each node"
  type        = map(string)
  default     = {}
}

variable "node_additional_zones" {
  type        = list(string)
  default     = []
  description = "The list of additional Google Compute Engine locations in which the cluster's nodes should be located. If additional zones are configured, the number of nodes specified in initial_node_count is created in all specified zones"
}

variable "region" {
  description = "Region"
  default     = "europe-west3"
}

variable "project" {
  description = "Project ID"
  default     = "fdc-core"
}
