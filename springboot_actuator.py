import re
import requests

from checks import AgentCheck

class SpringbootActuator(AgentCheck):

    GAUGE = "gauge"
    RATE  = "rate"

    GAUGE_PATTERN = r"gauge\."
    RATE_PATTERN  = r"counter\."

    BUILTIN_PATTERN = [
        (r"uptime", GAUGE),
        (r"instance\.uptime", GAUGE),
        (r"systemload.average", GAUGE),
        (r"processors", GAUGE),
        (r"mem\.?", GAUGE),
        (r"heap\.?", GAUGE),
        (r"gc\.", RATE),
        (r"threads\.?", GAUGE),
        (r"classes\.", RATE),
        (r"classes", GAUGE),
        (r"httpsessions\.", GAUGE),
        (r"datasource\.", GAUGE),
        (r"cache\.", GAUGE),
    ]

    def check(self, instance):
        if 'metrics_url' not in instance:
            self.log.info("Skipping instance, no metrics_url found.")
            return
        url = instance['metrics_url']

        default_timeout = self.init_config.get('default_timeout', 5)
        timeout = float(instance.get('timeout', default_timeout))

        self.tags = instance.get("tags", [])

        try:
            metrics = requests.get(url, timeout=timeout).json()
        except requests.exceptions.Timeout as e:
            self.log.critical(e)
            return

        for key, value in metrics.items():
            self.post(key, value)

    def post(self, key, value):
        if re.match(self.GAUGE_PATTERN, key):
            self.gauge("springboot.%s" % (key.replace("gauge.", "")), value, tags=self.tags)
            return
        elif re.match(self.RATE_PATTERN, key):
            self.rate("springboot.%s" % (key.replace("counter.", "")), value, tags=self.tags)
            return

        for p in self.BUILTIN_PATTERN:
            if re.match(p[0], key):
                name = "springboot.%s" % (key)
                if p[1] == self.RATE:
                    self.rate(name, value, tags=self.tags)
                else:
                    self.gauge(name, value, tags=self.tags)
                return

        self.log.warn("%s is not matched" % key)

