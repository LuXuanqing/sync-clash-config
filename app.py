import requests, logging, os, yaml, time
from dotenv import load_dotenv

load_dotenv(verbose=True)

logging.basicConfig(filename='dev.log',
                    filemode='w',
                    level=logging.DEBUG,
                    # format='%(levelname)s %(asctime)s %(name)s %(message)s',
                    format='%(asctime)s: [%(levelname)s] - [%(name)s] - %(message)s')
logger = logging.getLogger(__name__)

# 从jiyou下载配置文本
config_url = os.getenv('CONFIG_URL')
if not config_url:
    raise ValueError('can\'t find config url')


# TODO 保存为yaml_proxy文件

class YamlFile(object):

    def __init__(self, path):
        """

        Args:
            path (str): yaml文件的路径
        """
        self.__path = path
        self.text = ''
        # 如果path所指的文件存在，则读取，没有则新建
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
            logger.info('load_yaml {}'.format(path))
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


class Config(object):
    def __init__(self, path):
        self.__file = YamlFile(path)
        self.dict = {}
        self.load_yaml()

    def __repr__(self):
        return '<Config {}>'.format(self.__file.path)

    def load_yaml(self):
        self.dict = yaml.load(self.__file.text, Loader=yaml.FullLoader) or {}

    def download_yaml(self, url):
        self.__file.download(url)
        self.load_yaml()

    def uncomment(self):
        self.__file.uncomment()
        self.load_yaml()

    def save_file(self, path: str = None):
        self.__file.text = yaml.dump(self.dict, allow_unicode=True, sort_keys=False)
        self.__file.save(path)

    def update(self, **kw):
        self.dict.update(**kw)


# if __name__ == '__main__':
if True:
    config = Config('yaml/config.yaml')
    base_config = Config('yaml/base.yaml')
    rule_config = Config('yaml/rule.yaml')
    proxy_config = Config('yaml/jiyou-20200501020021.yaml')
    proxy_config.uncomment()

    config.update(**base_config.dict)

    # 删除fallback组
    del proxy_config.dict['Proxy Group'][2]
    # 第一组铂金改名为PROXY
    proxy_config.dict['Proxy Group'][0]['name'] = 'PROXY'
    # 第一组的首个服务器改为第二组（auto url-test）
    proxy_config.dict['Proxy Group'][0]['proxies'] = [proxy_config.dict['Proxy Group'][1]['name']] + \
                                                     proxy_config.dict['Proxy Group'][0]['proxies']
    config.update(**{
        'Proxy': proxy_config.dict['Proxy'],
        'Proxy Group': proxy_config.dict['Proxy Group']
    })

    config.update(Rule=rule_config.dict['Rule'])

    config.save_file()

    # TODO 配置文件同步到rspi
    # TODO rspi重载clash配置
