---
id: msg_gmail_e662720321cb
source: gmail
channel: email
sender: Grafana Labs <cloud-success@grafana.com>
subject: Kubernetes Monitoring – zero to full-cluster observability with Helm
timestamp: '2026-01-16T01:32:50'
status: pending
priority: normal
gmail_message_id: 19bc35c65b810e9d
gmail_thread_id: 19bc35c65b810e9d
labels:
- UNREAD
- CATEGORY_UPDATES
- INBOX
---
# Message from Grafana Labs <cloud-success@grafana.com>

**Subject**: Kubernetes Monitoring – zero to full-cluster observability with Helm

**Received**: 2026-01-16 01:32 AM

## Content

Grafana Labs ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvgL1ZafM1td3h9yULZWvEF0-3D5_MH_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BUAKYpYx2xICwcWoU0JcrixAsK-2F-2B3FgG23vjkVSWMeuBq4OqdZB9nL5kac9QKnq2DfdlZQ6yiFlfRpN-2BLB1uOXnPPiHiRvVRBlBUULFyoL-2FtCchUE-2F91l8bu1Nc-2FKTbb8A-3D )

****************************************************
Introducing Grafana Community Kubernetes Helm Charts
****************************************************

There's a new, fast and easy method for monitoring Kubernetes-based applications. Our Helm charts ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvhIT1H8-2BgWhaWu-2BK0nLqXyZGd9h7jUfgHbt7xMDSFMpkTl-2FQJdt9E2XM7lLIXGb-2BKjFwNjMoQXZ3e7ADZIYse5-2BtRFqFR6-2BYX3gwxf4qQMzOHklq_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BVPHReOFcvmfGC3e78AjLDV-2BtRQdCUmgOUpN-2BSEvhZZHVjdfKCRuoOnXU-2BlyXDM73QHddnV57hObZNPk5wooDchXTOVXUl1bHgz2atN6sTA8DYhafqPD4f-2FlfH3b5XhRAs-3D ) facilitate collecting and forwarding metrics, pod logs, and Kubernetes events to your fully-managed Grafana Cloud observability stack.

Using Helm, you can streamline the collection of telemetry data from your Kubernetes clusters. Use our charts to install the following four k8s monitoring tools: Grafana Agent, kube-state-metrics, Node Exporter, and OpenCost. These tools together will provide health and performance data from your clusters with minimal configuration and maintenance.

-----------------------------
Quick commands to get started
-----------------------------

* Setup the Grafana chart repository:
helm repo add grafana https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvjMOh2IEIOQiycH6iN8AQhrJnEP56Xx5EobHyCKBR-2BR-2BSeAv_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BUDFDG8gkpzQZy4F8ltritt0gwgvaoYHmiMDgpBO7vVi82yApSJt1MPm5-2Fy5PfbAIdW52GZZC1Na-2FVAi28ZnDP-2B4XGiSVIXUCm0KAJ7gd0-2B-2F2NV0uacTJ61RarAE0J0-2Bpw-3D
helm repo update
* Configure ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvhIT1H8-2BgWhaWu-2BK0nLqXyaZjUwFkmVfezIBgn3lKID7xY8foUprBmReckvmhjwTSoTap5ZlaTyJwCr0JmnikoCiIlwdVw28YylUt1racpfHxbG970n4tec-2FPS-2FPTm2vVA-3D-3Dx0Ag_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BXVHxCIRgsp6sSrRsr5do9x0BAIN6N377DUwo2KqMv8-2B6Q1AMKDEvzoPRn6wB2UjNxyD8Gh10Tyupgcx1KmpfuZI1gdXa83xTrMmGzFVgvHqs9Z-2BELLKHVap5iEFo0ezYE-3D ) the Grafana k8s Monitoring Chart

That's it. Once you've installed the Grafana k8s Monitoring Helm Chart, you'll be able to dive straight into:

* Out-of-the-box metrics
* Pre-configured dashboards & alerts
* Pod logs
* k8s events
* Cost monitoring insights
* Efficient reports

Deploy Grafana K8s Monitoring ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvhkw3JBRVYWd11EFjgViUr8Q-2BBx4ept3EQsMhmj3LLSu-2Bz5YhtGZD2Dmooybn09gWM4RcVncclgKkG3AaNqmoi0NWd0ziUWi7qQQh2GMbu1KDVcUexrxem-2F7bux2LPthmMC-2BHlgdI0Kp27mEzgdOEl69dzJx1xSDAdv-2F-2Few0v7RxHgGd_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BWAdSzc-2B2LmG9LekjlVbQ-2FWssl9pcNsxERGMbJ81HolrkYd6xPsI8WX3udm8oHwgP0bPJKOdZdVRwGrtfN9lmmPZXivaobwTljxwrU4jvYwEKObcUF42B9Wi-2FvalOvTKvM-3D )

If you have any questions about monitoring Kubernetes with Grafana Cloud, please reply to this email and we'll get back to you.

Regards,

Grafana Labs

Grafana Labs ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvgL1ZafM1td3h9yULZWvEF0-3DpFQs_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BVoCkifY35dpBsuiJ4qZKz31pXVyY0gfn53xJBQzDGq-2BhvoyJrsGRncWmHbFcDDq76x8j2KUmNmaLwNuHPkp2C1DaR9L3wp6I1JpFoSlxlFkwBVU6XHxzDQ7nK50ZE9BYQ-3D )

You received this email because you signed up for Grafana Cloud. You can unsubscribe ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvmWIbCICirAHFMQMaCf0amz0e7-2BexunVIqXfmBi62SwU1d3kZBSO8LXHWdiBigGmx3OJ4VcMqRxveLyDG1o4zh5RL4Xrr5RljxV71-2BVmyn7-2F0yyJ_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BVtMfBqPgzENO0UcbVn1f8MzNWhY-2BTbG0PM5RkLUkH-2FV3IUUJu9C9w7-2B7P1t0oYRStOkGLRYc4Pu3gjKvzi9juz03lbBrALdgVmfLfVA7aAc0aeMaOJFdOcD1UomKPf59s-3D ) or manage your preferences ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvmWIbCICirAHFMQMaCf0amyNtM7Brru-2BHRLwNVuP-2BbWgTnDpz-2FLDEl8omsWsl6hHsTR0hwpeEPa-2FLvUsDCpiZaYKG-2BcOO9IBWHXEhEM4Rt5jKtrJpIVVyKH4Mn0Y2uobwQ-3D-3Dkd8M_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BUvR-2FF-2BNVCn9CiI0bDXWJgNhYeBOqClKizjPpTUu8aDQanuPAdt7nWbbhhZ0W389ChICFwZa6qEZ4dVxbY5nhXt6MklRWt7RqgvTBFQRrcsHAzXdlosUEIQh-2B9uM2YOnaQ-3D ) to control the emails you receive.

Twitter ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvmIhOL-2BowsC-2BavLCAmjTg3uQUEl-2Fu-2Fccgo6z6GDh6BIBiUk0_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BWoT42Kuk9kN68-2B-2FG8Ly1TIpSG8aZaVei4RY6Gg9fpZrIyebqNngmbsOGSn8XXH1urH35KvZOP2LUTIYI-2B3MdCgm3RY-2FGpTrZkNsrC-2FGxFq84JJbri9WBzrVjxyAJNiZLo-3D )
LinkedIn ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvjsX0zbJsI614bquBKiaEziXTH5z5Pj-2FDpMNYZP3w-2B5j5mEILzfCu3fwH-2Fyf2TwPJQ-3D-3DSNKk_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BXoOgAHUVrfmtHlGLGtthHF35SWNn-2B0O-2BJ-2Bqa14STD9PhhHNrwYEr6VEDG3jNpI1x1SxEMXjwwCbAoyHHrHJq9R7AQIL7bptHtB4023hpj9-2FIg5XceKL0Nl20WqbIod5jg-3D )
Facebook ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvsTy-2FBsV-2Belsc2qVwOLLcQfAK2kolySE1NZrZxmJ9Os6Goj5_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BXRyUdOQZc4mLiCcUWw4DR4-2BbLym0lTfbRbwnDKY2o0b5XHsDkM6HN8ypzs4PJSWuPnZQNP-2Blkf5Ja5OfqQpD33DFjzFB8uk1Rb-2FxHiNOZuRogEcR-2B1v9Rj0Chn0JsoaXg-3D )
Dev ( https://u22025218.ct.sendgrid.net/ls/click?upn=u001.EfP4PuKIVDCIe-2Bmc2LSbvqzNr1DMkaZTzaZn4zx9rrO-2BBYp23f7LyJcDu5MocPXoK6Fy_lUQSHAw898v8pKPFvCcbZusrGcF6AwEMaxjjKGvdnVKoNjzdddBbqHeFgCVPiMfDPbgxR-2Bxc5WFi2Ln2NHDh8kGsadRAlcxUMrEiq-2BXOOOFOJSimdQLRxiz2ZyP0uQLczm2copsxlUvnNq2-2BJlFnwwiScp6miOD1x8F4kxHGJ-2BW8m7R31DiAMPn7yXbhB0sotToCLgvZ7sb-2Bgij-2BD7oX3VHM-2BPIo98pyoPvBV3JVVIC9VHeUI-2FZ2mAqVEd9YcMveWeT1TJm2RYTca-2Bbow0XQ9IhE8G2WI3fGQdFa9FyaKIE-3D )

## Suggested Actions

- [ ] Reply to sender
- [ ] Add to task list
- [ ] File in appropriate folder
- [ ] Mark as done

## Metadata

- **Source**: gmail
- **Channel**: email
- **Message ID**: 19bc35c65b810e9d
- **Thread ID**: 19bc35c65b810e9d
- **Labels**: UNREAD, CATEGORY_UPDATES, INBOX
- **Has Attachments**: No
