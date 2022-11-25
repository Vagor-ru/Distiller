class transferConfig(object):
    """Версия от 22.11.2022 сохранение предыдущей конфигурации"""
    def transfer(cfgNew, cfgOld):
        cfgNew['CONDER_PIN']['number']=cfgOld['CONDER_PIN']
        cfgNew['DEPH_PIN']['number']=cfgOld['DEPH_PIN']
        cfgNew['HEATER_PIN']['number']=cfgOld['HEATER_PIN']
        cfgNew['OW_PIN']['number']=cfgOld['OW_PIN']
        cfgNew['PARAMETERS']['Kdeph']['value']=(cfgOld['PARAMETERS']['Kdeph']+cfgOld['PARAMETERS']['Kdeph2'])/2
        cfgNew['PARAMETERS']['Kp']['value']=(cfgOld['PARAMETERS']['Kp']+cfgOld['PARAMETERS']['Kp2'])/2
        cfgNew['P_H2O']['value']=cfgOld['P_H2O']
        cfgNew['Tdephlock']['value']=cfgOld['Tdephlock']
        cfgNew['T_H2O']['value']=cfgOld['T_H2O']
        cfgNew['rTEH']['value']=cfgOld['rTEH']
        cfgNew['tCooling']['value']=cfgOld['tCooling']
        cfgNew['tA_F']['value']=cfgOld['tA_F']
        cfgNew['K_V']['value']=cfgOld['K_V']
        cfgNew['ADC_ADDR']['value']=cfgOld['ADC_ADDR']
        cfgNew['Tcond']=cfgOld['Tcond']
        cfgNew['tFillCoolers']=cfgOld['tFillCoolers']
        cfgNew['LOCATIONS']['names']=cfgOld['LOCATIONS']



