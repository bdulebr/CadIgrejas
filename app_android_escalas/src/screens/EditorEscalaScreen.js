/*
* PROJETO: Palavra de Vida Enseada - Intranet
* ARQUIVO: app_android_escalas/src/screens/EditorEscalaScreen.js
* DESCRIÇÃO: Código-fonte do módulo
* DEV: Marcos Roberto Lira (marcos@pvenseada.org)
* VERSÃO: 0.0.1
* DATA DA ÚLTIMA ALTERAÇÃO: 16/06/2026 14:37
* LOG DE ALTERAÇÕES:
* - 16/06/2026 14:37: Auditoria e padronização global (Goal)
*/
import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, FlatList, StyleSheet, ActivityIndicator, Alert } from 'react-native';
import api from '../api';

export default function EditorEscalaScreen({ route }) {
  const { comp_id, mes_ano } = route.params;
  const [escalas, setEscalas] = useState([]);
  const [loading, setLoading] = useState(true);

  const fetchEscalas = async () => {
    try {
      const response = await api.get(`/lider/competencias/${comp_id}/slots/`);
      setEscalas(response.data);
    } catch (error) {
      console.log(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchEscalas();
  }, [comp_id]);

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Text style={styles.data}>{item.data_escala} - {item.tipo_evento_display}</Text>
      <Text style={styles.funcao}>{item.funcao_nome}</Text>
      {item.membro_escalado ? (
        <Text style={styles.membroText}>✅ {item.membro_nome}</Text>
      ) : (
        <TouchableOpacity style={styles.btnAssign} onPress={() => Alert.alert('Alocação', 'Para selecionar via App, será necessário usar o ID do Membro ou usar o Motor de IA na Dashboard.')}>
          <Text style={styles.btnText}>Atribuir Membro</Text>
        </TouchableOpacity>
      )}
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Editor: {mes_ano}</Text>
      {loading ? <ActivityIndicator size="large" color="#3b82f6" /> : (
        <FlatList
          data={escalas}
          keyExtractor={(item) => item.id.toString()}
          renderItem={renderItem}
          ListEmptyComponent={<Text style={{color: '#9ca3af'}}>Nenhum slot gerado ainda. Use o Motor IA primeiro para pre-popular.</Text>}
        />
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#111827', padding: 20 },
  title: { fontSize: 24, fontWeight: 'bold', color: '#fff', marginBottom: 20 },
  card: { backgroundColor: '#1f2937', padding: 15, borderRadius: 12, marginBottom: 15 },
  data: { color: '#60a5fa', fontWeight: 'bold', marginBottom: 5 },
  funcao: { color: '#fff', fontSize: 16, marginBottom: 10 },
  membroText: { color: '#10b981', fontSize: 16, fontWeight: 'bold' },
  btnAssign: { backgroundColor: '#3b82f6', padding: 10, borderRadius: 6, alignItems: 'center' },
  btnText: { color: '#fff', fontWeight: 'bold' }
});
