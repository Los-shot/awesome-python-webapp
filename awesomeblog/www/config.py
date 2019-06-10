import config_default
configs = config_default.configs

try:
    def merge(src:dict,override:dict):
        if not override:
            return src

        def clone(a:dict):
            d = {}
            for k,v in a.items():
                if isinstance(v,dict):
                    d[k] = clone(v)
                else:
                    d[k] = v
            return d

        cfgs = clone(src)

        def cover(a:dict,b:dict):
            for k,v in a.items():
                o = b.get(k)
                if isinstance(o,dict):
                    cover(v,o)
                elif o:
                    a[k] = o

        cover(cfgs,override)
        
        return cfgs
    import config_override
    configs = merge(configs,config_override.configs)
except ImportError:
    pass

