import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator, Alert, TextInput } from 'react-native';
import api from '../api';

export default function CompetenciasScreen({ navigation }) {
  const [competencias, setCompetencias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [departamentos, setDepartamentos] = useState([]);
  const [novoMes, setNovoMes] = useState('');
  const [deptoAtivo, setDeptoAtivo] = useState(null);

  useEffect(() => {
    const init = async () => {
      try {
        const perf = await api.get('/perfil/me/');
        if(perf.data.departamentos_liderados && perf.data.departamentos_liderados.length > 0){
          setDepartamentos(perf.data.departamentos_liderados);
          setDeptoAtivo(perf.data.departamentos_liderados[0].id);
        }
        await fetchCompetencias();
      } catch (error) {
        console.log(error);
      }
    };
    init();
  }, []);

  const fetchCompetencias = async () => {
    try {
      const response = await api.get('/lider/competencias/');
      setCompetencias(response.data);
    } catch(e) {} finally { setLoading(false); }
  };

  const handleCreate = async () => {
    if(!novoMes || !deptoAtivo) {
      Alert.alert('Erro', 'Preencha o mês (Ex: 07/2026)');
      return;
    }
    setLoading(true);
    try {
      await api.post('/lider/competencias/', { mes_ano: novoMes, departamento_id: deptoAtivo });
      setNovoMes('');
      fetchCompetencias();
    } catch(e) {
      Alert.alert('Erro', 'Falha ao criar competência');
      setLoading(false);
    }
  };

  const renderItem = ({ item }) => (
    <TouchableOpacity
      style={styles.card}
      onPress={() => navigation.navigate('EditorEscala', { comp_id: item.id, mes_ano: item.mes_ano })}
    >
      <Text style={styles.compName}>{item.mes_ano} - {item.departamento_nome}</Text>
      <Text style={styles.status}>{item.status_display}</Text>
    </TouchableOpacity>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Gerenciar Meses/Escalas</Text>

      <View style={styles.form}>
        <TextInput
          style={styles.input}
          placeholder="Novo Mês (Ex: 08/2026)"
          placeholderTextColor="#9ca3af"
          value={novoMes}
          onChangeText={setNovoMes}
        />
        <TouchableOpacity style={styles.button} onPress={handleCreate}>
          <Text style={styles.buttonText}>+ Criar Rascunho</Text>
        </TouchableOpacity>
      </View>

      {loading ? <ActivityIndicator size="large" color="#3b82f6" /> : (
        <FlatList
          data={competencias}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 20 },
  form: { backgroundColor: '#1f2937', padding: 15, borderRadius: 12, marginBottom: 20 },
  input: { backgroundColor: '#374151', color: '#fff', padding: 12, borderRadius: 8, marginBottom: 10 },
  button: { backgroundColor: '#10b981', padding: 15, borderRadius: 8, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: 'bold' },
  card: { backgroundColor: '#374151', padding: 15, borderRadius: 12, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between' },
  compName: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  status: { color: '#fbbf24', fontSize: 14 }
});
