import requests, logging, os, yaml, time
from dotenv import load_dotenv

load_dotenv(verbose=True)

logging.basicConfig(filename='logs/{}.log'.format(time.strftime('%Y%m%d-%H%M%S')),
                    filemode='w',
                    level=logging.DEBUG,
                    format='%(asctime)s - %(name)s:%(lineno)s - %(funcName)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 从jiyou下载配置文本
config_url = os.getenv('CONFIG_URL')
if not config_url:
    raise ValueError('can\'t find config url')


# TODO 保存为yaml_proxy文件

class YamlFile(object):
    def __init__(self, path=None):
        """
        Args:
            path (str): yaml文件的路径
        """
        self.__path = path
        self.text = ''
        # 如果path所指的文件存在，则读取，没有则新建
        if path:
            if os.path.exists(path):
                self.read(path)
            else:
                self.save()

    def __repr__(self):
        return '<YamlFile {}>'.format(self.__path)

    @property
    def path(self):
        return self.__path

    def read(self, path: str):
        """
        读取yaml文件
        Args:
            path (str): 要读取的.yaml文件的路径
        """
        self.__path = path
        with open(path, encoding='UTF-8') as f:
            self.text = f.read()
            logger.info('loaded yaml {}'.format(path))
        return self

    def save(self, path: str = None):
        """
        写入yaml文件
        Args:
            path (str):
        """
        self.__path = path or self.__path
        with open(self.__path, 'w', encoding='UTF-8') as f:
            f.write(self.text)
            logger.info('{} saved: {}'.format(self.__path, self.text))

    def uncomment(self):
        self.text = self.text.replace('#', '')

    def download(self, url: str):
        """
        下载订阅的clash配置文件
        Args:
            url (str): 下载配置文件的url
        """
        response = requests.get(url)
        logger.info('downloaded config from {}'.format(url))
        self.text = response.text
        logger.debug('downloaded config: {}'.format(self.text))


class Config(object):
    def __init__(self, path):
        self.__path = path
        self.__text = ''
        self.dict = {}
        if os.path.exists(path):
            self.read()

    def __repr__(self):
        return '<Config {}>'.format(self.__path)

    def load(self):
        self.dict = yaml.load(self.__text, Loader=yaml.FullLoader) or {}
        logger.info('loaded dict from yaml')
        logger.debug('dict: {}'.format(self.dict))

    def read(self):
        with open(self.__path, encoding='UTF-8') as f:
            self.__text = f.read()
            logger.info('read yaml file {}'.format(self.__path))
            logger.debug('yaml text: {}'.format(self.__text))
            self.load()

    def download(self, url):
        response = requests.get(url)
        logger.info('downloaded {}'.format(url))
        self.__text = response.text
        logger.debug('downloaded config text: {}'.format(self.__text))
        self.load()

    def save(self, path=None):
        self.__path = path or self.__path
        self.__text = yaml.dump(self.dict, allow_unicode=True, sort_keys=False)
        logger.info('self.__text changed')
        logger.debug('__text: {}'.format(self.__text))
        with open(self.__path, 'w', encoding='UTF-8') as f:
            f.write(self.__text)
            logger.info('{} saved'.format(self.__path))


    def uncomment(self):
        logger.debug('__text: {}'.format(self.__text))
        self.__text = self.__text.replace('#', '')
        logger.info('uncommented')
        logger.debug('__text: {}'.format(self.__text))
        self.load()

    def update(self, **kw):
        self.dict.update(**kw)


if __name__ == '__main__':
    def process_jiyou(cfg):
        # 删除fallback组
        logger.debug('Proxy Group: {}'.format(cfg.dict['Proxy Group']))
        logger.debug('Proxy Group-2-name: {}'.format(cfg.dict['Proxy Group'][2]['name']))
        del cfg.dict['Proxy Group'][2]
        # 第一组铂金改名为PROXY
        cfg.dict['Proxy Group'][0]['name'] = 'PROXY'
        # 第一组的首个服务器改为第二组（auto url-test）
        cfg.dict['Proxy Group'][0]['proxies'] = [cfg.dict['Proxy Group'][1]['name']] + cfg.dict['Proxy Group'][0][
            'proxies']


    base_cfg = Config('yaml/base.yaml')
    rule_cfg = Config('yaml/rule.yaml')
    proxy_cfg = Config('yaml/jiyou.yaml')
    cfg = Config('yaml/config-{}.yaml'.format(time.strftime('%Y%m%d-%H%M%S')))

    proxy_cfg.download(os.getenv('CONFIG_URL'))
    proxy_cfg.uncomment()
    proxy_cfg.save()
    process_jiyou(proxy_cfg)

    cfg.update(**base_cfg.dict)
    cfg.update(**{
        'Proxy': proxy_cfg.dict['Proxy'],
        'Proxy Group': proxy_cfg.dict['Proxy Group']
    })
    cfg.update(Rule=rule_cfg.dict['Rule'])

    # TODO 把旧的config.yaml重命名为config-time.yaml
    cfg.save(os.getenv('TARGET_PATH'))

    # TODO 配置文件同步到rspi
    # TODO rspi重载clash配置
