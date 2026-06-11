import React, { useEffect, useState } from 'react';
import { View, Text, FlatList, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import api from '../api';

export default function EscalaDepartamentoScreen() {
  const [escalas, setEscalas] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEscalas = async () => {
    try {
      const response = await api.get('/escalas/departamento/');
      setEscalas(response.data);
    } catch (error) {
      console.log('Erro ao buscar escalas do depto', error);
      Alert.alert('Erro', 'Não foi possível carregar a escala do departamento');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalas();
  }, []);

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.dateBadge}>
          <Text style={styles.dateText}>{item.data_escala}</Text>
        </View>
        <Text style={styles.timeText}>{item.horario_inicio} às {item.horario_fim}</Text>
      </View>
      <Text style={styles.evento}>{item.tipo_evento_display} - {item.departamento_nome}</Text>
      <View style={styles.footerRow}>
        <Text style={styles.membroText}>👤 {item.membro_nome}</Text>
        <View style={styles.funcaoBadge}>
          <Text style={styles.funcaoText}>{item.funcao_nome}</Text>
        </View>
      </View>
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Escala Pública (Depto)</Text>
      {loading ? (
        <ActivityIndicator size="large" color="#3b82f6" style={{ marginTop: 20 }} />
      ) : (
        <FlatList
          data={escalas}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          contentContainerStyle={{ paddingBottom: 20 }}
          ListEmptyComponent={<Text style={styles.empty}>Nenhuma escala publicada encontrada para seu departamento.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 20, marginTop: 40 },
  empty: { color: '#9ca3af' },
  card: { backgroundColor: '#1f2937', padding: 15, borderRadius: 12, marginBottom: 15, borderColor: '#374151', borderWidth: 1 },
  headerRow: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 10 },
  dateBadge: { backgroundColor: 'rgba(59, 130, 246, 0.2)', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 6 },
  dateText: { color: '#60a5fa', fontWeight: 'bold', fontSize: 12 },
  timeText: { color: '#9ca3af', fontSize: 12 },
  evento: { fontSize: 16, fontWeight: 'bold', color: '#fff', marginBottom: 10 },
  footerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  membroText: { color: '#10b981', fontSize: 14, fontWeight: 'bold' },
  funcaoBadge: { backgroundColor: '#111827', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 12 },
  funcaoText: { color: '#9ca3af', fontSize: 12 }
});
