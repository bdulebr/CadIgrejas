import React, { useEffect, useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, FlatList, StyleSheet, Alert, ActivityIndicator } from 'react-native';
import api from '../api';

export default function AusenciasScreen() {
  const [ausencias, setAusencias] = useState([]);
  const [loading, setLoading] = useState(true);
  const [motivo, setMotivo] = useState('');
  const [dataInicio, setDataInicio] = useState('');
  const [dataFim, setDataFim] = useState('');

  const fetchAusencias = async () => {
    try {
      const response = await api.get('/escalas/ausencias/');
      setAusencias(response.data);
    } catch (error) {
      console.log('Erro ao buscar', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAusencias();
  }, []);

  const handleSalvar = async () => {
    if(!motivo || !dataInicio || !dataFim){
      Alert.alert('Erro', 'Preencha todos os campos (Data no formato YYYY-MM-DD)');
      return;
    }
    setLoading(true);
    try {
      await api.post('/escalas/ausencias/', {
        motivo,
        data_inicio: dataInicio,
        data_fim: dataFim
      });
      Alert.alert('Sucesso', 'Ausência registrada!');
      setMotivo(''); setDataInicio(''); setDataFim('');
      fetchAusencias();
    } catch (error) {
      Alert.alert('Erro', 'Falha ao salvar. Verifique o formato da data (YYYY-MM-DD)');
      setLoading(false);
    }
  };

  const handleRemover = async (id) => {
    setLoading(true);
    try {
      await api.delete(`/escalas/ausencias/${id}/`);
      fetchAusencias();
    } catch (error) {
      Alert.alert('Erro', 'Falha ao remover');
      setLoading(false);
    }
  };

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View>
        <Text style={styles.motivo}>{item.motivo}</Text>
        <Text style={styles.datas}>{item.data_inicio} até {item.data_fim}</Text>
      </View>
      <TouchableOpacity style={styles.deleteBtn} onPress={() => handleRemover(item.id)}>
        <Text style={styles.deleteText}>X</Text>
      </TouchableOpacity>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Registro de Ausências</Text>

      <View style={styles.form}>
        <TextInput style={styles.input} placeholder="Motivo (Ex: Viagem)" placeholderTextColor="#9ca3af" value={motivo} onChangeText={setMotivo} />
        <View style={{flexDirection: 'row', justifyContent: 'space-between'}}>
          <TextInput style={[styles.input, {flex: 0.48}]} placeholder="Início (YYYY-MM-DD)" placeholderTextColor="#9ca3af" value={dataInicio} onChangeText={setDataInicio} />
          <TextInput style={[styles.input, {flex: 0.48}]} placeholder="Fim (YYYY-MM-DD)" placeholderTextColor="#9ca3af" value={dataFim} onChangeText={setDataFim} />
        </View>
        <TouchableOpacity style={styles.button} onPress={handleSalvar}>
          <Text style={styles.buttonText}>Registrar Ausência</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.subtitle}>Ausências Ativas</Text>
      {loading ? (
        <ActivityIndicator size="large" color="#3b82f6" />
      ) : (
        <FlatList
          data={ausencias}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          ListEmptyComponent={<Text style={{color: '#9ca3af'}}>Nenhuma ausência.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 20, marginTop: 40 },
  subtitle: { fontSize: 16, fontWeight: 'bold', color: '#9ca3af', marginBottom: 10, marginTop: 20 },
  form: { backgroundColor: '#1f2937', padding: 15, borderRadius: 12 },
  input: { backgroundColor: '#374151', color: '#fff', padding: 12, borderRadius: 8, marginBottom: 10 },
  button: { backgroundColor: '#3b82f6', padding: 15, borderRadius: 8, alignItems: 'center' },
  buttonText: { color: '#fff', fontWeight: 'bold' },
  card: { backgroundColor: '#1f2937', padding: 15, borderRadius: 12, marginBottom: 10, flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  motivo: { color: '#fff', fontWeight: 'bold', fontSize: 16 },
  datas: { color: '#9ca3af', fontSize: 12, marginTop: 4 },
  deleteBtn: { backgroundColor: 'rgba(239, 68, 68, 0.2)', width: 30, height: 30, borderRadius: 15, alignItems: 'center', justifyContent: 'center' },
  deleteText: { color: '#ef4444', fontWeight: 'bold' }
});
