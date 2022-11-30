class transferConfig(object):
    """Версия от 22.11.2022 сохранение предыдущей конфигурации"""
    def transfer(cfgNew, cfgOld):
        cfgNew['CONDER_PIN']['number']=cfgOld['CONDER_PIN']
        cfgNew['DEPH_PIN']['number']=cfgOld['DEPH_PIN']
        cfgNew['HEATER_PIN']['number']=cfgOld['HEATER_PIN']
        cfgNew['OW_PIN']['number']=cfgOld['OW_PIN']
        cfgNew['PARAMETERS']['Kdeph']['value']=(cfgOld['PARAMETERS']['Kdeph']+cfgOld['PARAMETERS']['Kdeph2'])/2
        cfgNew['PARAMETERS']['Kp']['value']=(cfgOld['PARAMETERS']['Kp']+cfgOld['PARAMETERS']['Kp2'])/2
        cfgNew['PARAMETERS']['P_H2O']['value']=cfgOld['PARAMETERS']['P_H2O']
        cfgNew['PARAMETERS']['Tdephlock']['value']=cfgOld['PARAMETERS']['Tdephlock']
        cfgNew['PARAMETERS']['T_H2O']['value']=cfgOld['PARAMETERS']['T_H2O']
        cfgNew['PARAMETERS']['rTEH']['value']=cfgOld['PARAMETERS']['rTEH']
        cfgNew['PARAMETERS']['tCooling']['value']=cfgOld['PARAMETERS']['tCooling']
        cfgNew['PARAMETERS']['tA_F']['value']=cfgOld['PARAMETERS']['tA_F']
        cfgNew['PARAMETERS']['K_V']['value']=cfgOld['PARAMETERS']['K_V']
        cfgNew['ADC_ADDR']['value']=cfgOld['ADC_ADDR']
        cfgNew['PARAMETERS']['Tcond']=cfgOld['PARAMETERS']['Tcond']
        cfgNew['PARAMETERS']['tFillCoolers']=cfgOld['PARAMETERS']['tFillCoolers']
        cfgNew['LOCATIONS']['names']=cfgOld['LOCATIONS']
        cfgNew['LOCATIONS']['locations']=cfgOld['T_LOCATIONS']



