import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet, ActivityIndicator, Alert, FlatList } from 'react-native';
import api from '../api';

export default function LiderScreen({ navigation }) {
  const [departamentos, setDepartamentos] = React.useState([]);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const fetchPerfil = async () => {
      try {
        const response = await api.get('/perfil/me/');
        setDepartamentos(response.data.departamentos_liderados || []);
      } catch (error) {
        console.log(error);
      } finally {
        setLoading(false);
      }
    };
    fetchPerfil();
  }, []);

  const rodarIA = async (deptoId, nome) => {
    Alert.alert('Iniciando IA', 'Gerando...');
    try {
      await api.post('/escalas/motor-ia/', { departamento_id: deptoId });
      Alert.alert('Sucesso', `Motor IA rodou com sucesso para ${nome}!`);
    } catch (error) {
      Alert.alert('Erro', 'Não foi possível rodar o motor.');
    }
  };

  if (loading) {
    return <View style={styles.container}><ActivityIndicator size="large" color="#3b82f6" /></View>;
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Painel do Líder</Text>

      <View style={styles.grid}>
        <TouchableOpacity style={styles.gridBtn} onPress={() => navigation.navigate('LiderMembros')}>
          <Text style={styles.gridText}>👥 Membros</Text>
        </TouchableOpacity>
        <TouchableOpacity style={styles.gridBtn} onPress={() => navigation.navigate('Competencias')}>
          <Text style={styles.gridText}>📅 Editor Escala</Text>
        </TouchableOpacity>
      </View>

      <Text style={styles.subtitle}>Gerar Escala Automática (IA)</Text>
      <FlatList
        data={departamentos}
        keyExtractor={(item) => item.id.toString()}
        renderItem={({ item }) => (
          <View style={styles.card}>
            <Text style={styles.deptoName}>{item.nome}</Text>
            <TouchableOpacity style={styles.aiButton} onPress={() => rodarIA(item.id, item.nome)}>
              <Text style={styles.aiButtonText}>Rodar Motor Groq (30 dias)</Text>
            </TouchableOpacity>
          </View>
        )}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 20, marginTop: 40 },
  subtitle: { fontSize: 18, fontWeight: 'bold', color: '#9ca3af', marginBottom: 15, marginTop: 20 },
  grid: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 20 },
  gridBtn: { backgroundColor: '#374151', padding: 20, borderRadius: 12, flex: 0.48, alignItems: 'center' },
  gridText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  card: { backgroundColor: '#1f2937', padding: 20, borderRadius: 12, marginBottom: 15 },
  deptoName: { color: '#fff', fontSize: 18, fontWeight: 'bold', marginBottom: 15 },
  aiButton: { backgroundColor: '#8b5cf6', padding: 15, borderRadius: 8, alignItems: 'center' },
  aiButtonText: { color: '#fff', fontWeight: 'bold' }
});
