$TTL 86400
@       IN      SOA     terrerov.com. terrerov.gmail.com. (
                        2024011501  ; Serial
                        3600        ; Refresh
                        1800        ; Retry
                        604800      ; Expire
                        86400 )     ; Minimum TTL

@       IN      NS      ns.terrerov.com.
@       IN      A       172.18.0.2
ns      IN      A       172.18.0.2

; Service records
www     IN      A       172.18.0.2
traefik IN      A       172.18.0.2
db      IN      A       172.18.0.4
monitor IN      A       172.18.0.2