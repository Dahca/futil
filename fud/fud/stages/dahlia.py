from fud.stages import Stage, Step, SourceType


class DahliaStage(Stage):
    def __init__(self, config):
        super().__init__('dahlia', 'futil', config,
                         'Compiles a Dahlia program to FuTIL')

    def _define(self):
        main = Step(SourceType.Path)
        main.set_cmd(f'{self.cmd} {{ctx[input_path]}} -b futil --lower')
        return [main]
