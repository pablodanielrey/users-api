import os
from autobahn.asyncio.wamp import ApplicationSession, ApplicationRunner


class Test(ApplicationSession):

    async def onJoin(self, details):
        print("onJoin")
        try:
            res = await self.call('project.func1', param1, param2, param3)
            print("call result: {}".format(res))
        except Exception as e:
            print("call error: {0}".format(e))


if __name__ == '__main__':

    print(os.environ)

    runner = ApplicationRunner(
        url=os.environ['CROSSBAR_URL'],
        realm=os.environ['CROSSBAR_REALM']
    )
    runner.run(Test)
