# frozen_string_literal: true

require 'csv'
require 'fileutils'

job = <<~JOB
  ---
  apiVersion: batch/v1
  kind: Job
  metadata:
    name: <SERVICE_NAME>
    labels:
      app: <SERVICE_NAME>
  spec:
    template:
      spec:
        containers:
        - name: <SERVICE_NAME>
          image: eu.gcr.io/strange-metrics-258802/jobs/mktdata-archiver:v0.1.0-a25a3f7
          imagePullPolicy: Always
          env:
          - name: SERVICE_HOSTNAME
            valueFrom:
              fieldRef:
                fieldPath: metadata.name
          - name: GOOGLE_APPLICATION_CREDENTIALS
            value: /etc/gcp/sa_credentials.json
          - name: LOG_LEVEL
            value: INFO
          - name: REDIS_NODE_ADDR
            value: "redis"
          - name: REDIS_NODE_TCP_PORT
            value: "6379"
          - name: COREPACK_FAMILIES
            value: ""
          - name: EXCHANGES
            value: "ftx,gateio"
          - name: MARKETS_FILTER
            value: "<MARKETS_FILTER>"
          - name: ARCHIVE_DATES
            value: "<ARCHIVE_DATES>"
          - name: MARKETS_CSV
            value: "/srv/app/markets.csv"
          - name: FTXKEY
            value: ""
          - name: FTXSECRET
            value: ""
          envFrom:
          - secretRef:
              name: mktdata-archiver
              optional: true
          volumeMounts:
            - name: service-account-credentials-volume
              mountPath: /etc/gcp
              readOnly: true
          resources:
            requests:
              cpu: 300m
              memory: 12Gi
            limits:
              cpu: 1000m
              memory: 30Gi
        volumes:
          - name: service-account-credentials-volume
            secret:
              secretName: mktdata-archiver-gcs
              items:
              - key: sa_json
                path: sa_credentials.json
        restartPolicy: Never
        nodeSelector:
          cloud.google.com/gke-nodepool: "argo-pool-v1"
          cloud.google.com/gke-preemptible: "true"
        tolerations:
          - key: "argo"
            operator: "Equal"
            value: "true"
            effect: "NoSchedule"
JOB

CSV.foreach('jobs.csv') do |row|
  puts row[0]
  row[1].split(',').each do |market|
    next if %w[BTCUSDP ETHUSDP EOSUSDP BNBUSDP].include?(market)
    # skip processed
    next if %w[ADAUSDP ADAU19 ADAZ19 ADAH20 ADAHM20].include?(market)
    next if %w[ALGOU19 ALGOZ19 ALGOH20 ALGOM20 ALGOUSDP].include?(market)
    next if %w[TRYBZ19 TRYBH20 TRYBM20 TRYBUSDP].include?(market)

    service_name = market.downcase + '-' + row[0]
    folder = 'raw_jobs/' + market
    j = job.gsub(/<SERVICE_NAME>/, service_name)
    j = j.gsub(/<MARKETS_FILTER>/, market)
    j = j.gsub(/<ARCHIVE_DATES>/, row[0])
    FileUtils.mkdir_p folder
    File.open(folder + '/' + row[0] + '.yaml', 'w') { |file| file.puts j }
  end
end
