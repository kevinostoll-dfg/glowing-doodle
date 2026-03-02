{{/*
Expand the name of the chart.
*/}}
{{- define "call-intelligence.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "call-intelligence.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "call-intelligence.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "call-intelligence.labels" -}}
helm.sh/chart: {{ include "call-intelligence.chart" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: call-intelligence
{{- end }}

{{/*
Selector labels for a component
*/}}
{{- define "call-intelligence.selectorLabels" -}}
app.kubernetes.io/name: {{ include "call-intelligence.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Database URL
*/}}
{{- define "call-intelligence.databaseUrl" -}}
postgresql://{{ .Values.postgresql.auth.username }}:{{ .Values.postgresql.auth.password }}@{{ include "call-intelligence.fullname" . }}-postgresql:5432/{{ .Values.postgresql.auth.database }}
{{- end }}

{{/*
Redis URL
*/}}
{{- define "call-intelligence.redisUrl" -}}
redis://{{ include "call-intelligence.fullname" . }}-redis-master:6379/0
{{- end }}
