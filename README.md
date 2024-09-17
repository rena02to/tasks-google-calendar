# Tarefas com o Google Calendar

O projeto consiste em uma API Restful que tem como objetivo realizar a criação de eventos, de forma integrada ao Google Calendar. Isto é, os eventos criados na aplicação, serão refletidos no Google agenda do usuário.

Neste projeto a tarefa pode ser:

- Criada
- Visualizada
- Editada
- Deletada

Considerando que no escopo do projeto ficou definido que o projeto será executado somente localmente, não usaremos autenticação e autorização como sugere o guia fornacido pela Google em seu [Guia de início rápido](https://developers.google.com/calendar/api/quickstart/python?hl=pt-br), a autenticação será baseada no JWT e no token gerado pela api do Google Calendar para cada usuário.

## Stack utilizada

![Django](https://skillicons.dev/icons?i=django "Django")

## Rodando localmente

1. Instale/verifique os pacotes necessários
    1. Verifique a instalação do Git
    ```
    git --version
    ```
    Caso apareça a versão do Git instalada em sua máquina, siga para o próximo passo, caso não, faça o dowload em [https://git-scm.com/download/](https://git-scm.com/download/). Após o download ser concluído, execute o arquivo, e finalize a instalação.

    2. Verifique a instalação do Python
    ```
    python --version
    ```
    
    Caso apareça a versão do Python instalada em sua máquina, siga para o próximo passo, caso não, faça o dowload em [https://www.python.org/downloads/](https://www.python.org/downloads/). Após o download ser concluído, execute o arquivo, e finalize a instalação.

    3. Verifique a instalação do Pip
    ```
    pip --version
    ```

    Caso apareça a versão do Pip instalada em sua máquina, siga para o próximo passo, caso não, execute os seguintes comandos:
```
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
```
```
python get-pip.py
```

4. Clone o projeto
```bash
  git clone https://github.com/rena02to/tasks-google-calendar.git
```

5. Entre no diretório do projeto
```bash
  cd tasks-google-calendar
```

6. (OPCIONAL) Caso não queira instalar as dependências diretamente em sua máquina, utilize a Virtualenv para criar um ambiente virtual. Assim, as dependências ficarão isoladas e não afetarão as configurações e pacotes do sistema operacional principal. Você pode instalar e usar a Virtualenv seguindo os passos abaixo, mas caso queira instalar as dependências em seu sistema operacional principal, pule para o passo 7.
    
    1. Instale a Virtualenv
    ```bash
    pip install virtualenv
    ```

    2. Crie a Virtualenv
    ```bash
    python -m venv venv
    ```

    3. Ative a Virtualenv
    ```bash
    venv\Scripts\activate
    ```

    Caso você receba um retorno similar a:

    ```
    (venv) PS C:\caminho\relativo\tasks-google-calendar>
    ```
    Pode seguir para o próximo passo. Porém, caso receba um retorno similar a:
    
    ```
    venv\Scripts\activate : O arquivo C:\caminho\relativo\tasks-google-calendar\venv\Scripts\activate.ps1 não pode ser carregado porque a execução de scripts foi desabilitada neste sistema. Para obter mais informações, consulte about_Execution_Policies em https://go.microsoft.com/fwlink/?LinkID=135170.
    No linha:1 caractere:1
    + venv\Scripts\activate
    + ~~~~~~~~~~~~~~~~~~~~~
    + CategoryInfo          : ErrodeSegurança: (:) [], PSSecurityException
    + FullyQualifiedErrorId : UnauthorizedAccess
    ```
    Execute o seguinte comando para resolver:
    
    ```
    Set-ExecutionPolicy RemoteSigned
    ```
    Quando questionado se deseja mudar a política de scripts, digite A (para "Sim para todos").

7. Instale as dependências
```
pip install -r requirements.txt
```

8. Aplique as migrations:
```
python manage.py migrate
```

9. Para acessar o DB do Django, rode o comando a seguir e crie um `super usuário`, após isso é só acessar a URL base (citada mais abaixo) seguido de `/admin` (a URL será algo como `http:localhost:8000/admin`):
```
python manage.py createsuperuser
```

10. Rode o servidor
```
python manage.py runserver
```

Se a porta 8000 de sua máquina estiver disponível, o projeto irá rodar no endereço `http://localhost:8000`, caso a porta 8000 não esteja disponível, ao rodar o projeto o django retornará o endereço no qual o projeto estará rodando localmente. Todas as requisições usarão como base tal URL (`http://localhost:<porta>/...`)

Como definição de projeto, todas as requisições seram feitas por meio de aplicações como o Imsonia ou Postman, portanto, consideraremos isso.

## Documentação da API

#### Autenticação
```http
  POST /api/login
```
Abre o navegador para que seja realizado o processo de autenticação com a conta do Google. Retorna o status, uma mensagem com o status da solicitação e um token de acesso que deverá ser usado nas requisições feitas para views protegidas (no nosso caso, todas as views exceto a de login são protegidas).

Para fazer login com uma conta diferente, basta realizar uma nova requisição para a mesma URL e salvar o token gerado. Assim, se quiser alternar entre contas, é necessário apenas utilizar o token correspondente à conta desejada ao realizar futuras requisições.

Em todas as URLs a seguir, na área de Authorization **DEVERÁ** ser selecionado Bearer Token e o token retornado no processo de login deverá ser colocado, pois esse é o processo de autenticação da aplicação, sem isso será retornado o erro `401`, que se acesso não autorizado.

#### Cria um evento
```http
  POST /api/create/
```
Nessa URL, na seção de `body` será necessário selecionar JSON colocar o seguinte formato de conteúdo, no qual **nenhum campo poderá ser omitido, podendo alguns deles ser nulos, os quais devem ser representados por uma string vazia** ```("campo": "")```. Caso o evento seja criado com sucesso será retornado o status, uma mensagem com o status, o id da task e o link para ela no Google Agenda, caso ocorra um erro, será exibido o erro.

Segue o formato:
```json
{
    "title": string,
    "description": string,
    "locale": string,
    "full_day": boolean,
    "start_date": string,
    "start_hour": string,
    "end_date": string,
    "end_hour": string,
    "participants": array,
    "reminders": array,
    "appellant": boolean,
    "recurrence": string
}
```
Segue descrição de como deve ser cada um dos valores
| Parâmetro   | Tipo       | Descrição                                   |
| :---------- | :--------- | :------------------------------------------ |
| `title`      | `string` | O título do evento que você deseja criar (**`Obrigatório`**)|
| `description`      | `string` | A descrição do evento que você deseja criar (**`Anulável`**) |
| `locale`      | `string` | O local onde irá ocorrer o evento (**`Anulável`**) |
| `full_day`      | `boolean` | Se o evento é um evento que dura o dia todo, ou não. Caso o evento dure o dia todo, "full_day": True, caso contrário, "full_day": False (**`Obrigatório`**) |
| `start_date`      | `string` | A data de início do evento. **Deve ter o formato AAAA-MM-DD** no qual AAAA é o ano com 4 dígitos, MM é o mês com 2 dígitos, DD o dia com 2 digitos. Por exemplo, 02 de março de 2024 deverá ficar no seguinte formato 2024-03-02 (**`Obrigatório`**) |
| `start_hour`      | `string` | Hora que o evento irá começar. **Deve ter o formato HH:MM:SS** no qual HH são as horas, MM os minutos e SS os segundos. Por exemplo, um evento que comecará às 09 horas, 30 minutos e 50 segundos deverá ficar no seguinte formato 09:30:00 (**`Anulável somente se "full_day": False`**, se esse campo for omitido, será definido o valor padrão para início do evento, que é 09:00:00)|
| `end_date`      | `string` | A data de término do evento. **Deve ter o formato AAAA-MM-DD** no qual AAAA é o ano com 4 dígitos, MM é o mês com 2 dígitos, DD o dia com 2 digitos. Por exemplo, 02 de março de 2024 deverá ficar no seguinte formato 2024-03-02 (**`Obrigatório`**)  |
| `end_hour`      | `string` | Hora que o evento irá terminar. **Deve ter o formato HH:MM:SS** no qual HH são as horas, MM os minutos e SS os segundos. Por exemplo, um evento que terminará às 11 horas deverá ficar no seguinte formato 11:00:00 (**`Anulável somente se "full_day": False`**, se esse campo for omitido, será definido o valor padrão para término do evento, que é 10:00:00 |
| `participants`      | `array` | Os participantes que você deseja adicionar no evento. **Deverá ter o formato: `"participants": [{"email": "participante1@email.com"}, {"email": "participante2@email.com"}]`**, no qual cada e-mail se refere ao e-mail de um participante. (**`Anulável`**) |
| `reminders`      | `array` | Os métodos pelo qual você deseja receber as notificações sobre o evento. **Deverá ter o seguinte formato: `"reminders": [{"method": string, "minutes": int}, {"method": string, "minutes": int}]`**, no qual a string que corresponde ao `method` pode ser o valor `"email"` ou `"popup"`, e o valor inteiro que corresponde a `minutes` é o número de minutos antes do evento que o você será avisado. (`Anulável`) |
| `appellant`      | `array` | Se o evento é recorrente. iso é, se o evento acontece mais de uma vez ou se é somente no dia definido. |
| `recurrence`      | `string` | A string de recorrência do evento. Essa string representa a recorrência do evento. A string se divide em algumas partes que estarão explicadas na tabela abaixo.

Tabela de definição da string de recorrência
| Parâmetro   | Descrição                                   |
| :---------- | :------------------------------------------ |
| `RRULE`      | Parte obrigatória da string de recorrência. Indica que a string contém uma regra de recorrência. |
| `FREQ`      | Exceto essa parte e a anterior, todo o resto é opcional e pode ser separado por um `;`. Define a frequência com que o evento deve ocorrer. Pode ser: `DAILY`: Diariamente, `WEEKLY`: Semanalmente, `MONTHLY`: Mensalmente, `YEARLY`: Anualmente |
| `COUNT`      | Especifica o número total de ocorrências do evento. Por exemplo, se COUNT=10, o evento ocorrerá 10 vezes na frequência definida em `FREQ` |
| `INTERVAL`      | Define o intervalo entre as ocorrências. Por exemplo: `INTERVAL=2` para eventos que ocorrem a cada 2 dias, semanas, meses ou anos, dependendo de `FREQ` |
| `UNTIL`      | Define uma data e hora até quando a regra de recorrência deve ser aplicada. Exemplo: `UNTIL=20240930T090000Z` para parar a recorrência em 30 de setembro de 2024 às 09:00 UTC.|
| `BYDAY`      | Especifica os dias da semana em que o evento deve ocorrer. Exemplo: `BYDAY=MO,TU,WE` para eventos que ocorrem nas segundas, terças e quartas-feiras. |
| `BYMONTHDAY`      | Especifica os dias do mês em que o evento deve ocorrer. Exemplo: `BYMONTHDAY=15` para eventos que ocorrem no 15º dia de cada mês. |
| `BYYEARDAY`      | Especifica o dia do ano em que o evento deve ocorrer. Exemplo: `BYYEARDAY=100` para o 100º dia do ano. |
| `BYYEARMONTH`      | Especifica os meses do ano em que o evento deve ocorrer. Exemplo: `BYYEARMONTH=3,6,9` para março, junho e setembro. |


Segue alguns exemplos:

- Diariamente por 10 vezes: `RRULE:FREQ=DAILY;COUNT=10`;
- Semanalmente às segundas e quartas-feiras por 6 semanas: `RRULE:FREQ=WEEKLY;BYDAY=MO,WE;COUNT=6`;
- Mensalmente no dia 15 até 30 de dezembro de 2024: `RRULE:FREQ=MONTHLY;BYMONTHDAY=15;UNTIL=20241230T235959Z`;
- Anualmente no 1º de janeiro e 25 de dezembro: `RRULE:FREQ=YEARLY;BYMONTHDAY=1,25;BYMONTH=1,12`

Segue alguns exemplos de eventos:
- Um evento com o título de "Assistir Matrix no cinema", com a descrição "O filme comecará às 21h. Terei que comprar pipoca e refrigerantes, deverei chegar 30 minutos antes.", que será no local "Parque Shopping - CineSystem", que não será o dia todo, será no dia 17 de novembro de 2024, comecará às 21h e terminará às 23:30h, terá como participantes o usuário esposa@email.com e filho@email.com, não será recorrente e deverá ser avisado 1 dia antes por e-mail e 2 horas antes por notificação de popup, ficaria da seguinte forma:
```json
    "title": "Assistir Matrix no cinema",
    "description": "O filme comecará às 21h. Terei que comprar pipoca e refrigerantes, deverei chegar 30 minutos antes.",
    "locale": "Parque Shopping - CineSystem",
    "full_day": false,
    "start_date": "2024-11-17",
    "start_hour": "21:00:00",
    "end_date": "2024-11-17",
    "end_hour": "23:30:00",
    "participants":[
        {"email": "esposa@email.com"},
        {"email": "filho@email.com"},
    ],
    "reminders": [
        {"method": "email", "minutes": 1440},
        {"method": "popup", "minutes": 120}
    ],
    "appellant": false,
    "recurrence": ""
```

- Um evento com o título de "Aula de informática", sem descrição, que será no online, que não será o dia todo, será no dia 17 de novembro de 2024, comecará às 14h e terminará às 17h, terá como participantes o professor que tem o email professor@email.com, será recorrente nas segundas e quintas até o dia 30 de dezembro de 2025 e deverá ser 30 minutos antes por notificação de popup, ficaria da seguinte forma:
```json
    "title": "Aula de informática",
    "description": "",
    "locale": "Online",
    "full_day": false,
    "start_date": "2024-11-17",
    "start_hour": "14:00:00",
    "end_date": "2024-11-17",
    "end_hour": "17:00:00",
    "participants":[
        {"email": "professor@email.com"},
    ],
    "reminders": [
        {"method": "popup", "minutes": 30}
    ],
    "appellant": true,
    "recurrence": "RRULE:FREQ=WEEKLY;BYDAY=MO,TH;UNTIL=20251230T235959Z"
```

- Um evento com o título de "Natal", sem descrição, que será o dia todo, será no dia 25 de dezembro, todos os anos, e deverá ser avisado 30 minutos antes, por popup (às 23:30:00 do dia 24 de dezembro) ficará da seguinte maneira:
```json
    "title": "Natal",
    "description": "",
    "locale": "",
    "full_day": true,
    "start_date": "2024-12-25",
    "start_hour": "",
    "end_date": "2024-12-25",
    "end_hour": "",
    "participants":[],
    "reminders": [
        {"method": "popup", "minutes": 30}
    ],
    "appellant": true,
    "recurrence": "RRULE:FREQ=YEARLY;"
```


#### Retorna todos os eventos de um usuário
```http
  GET /api/get_all_tasks/
```
Ao realizar a requisição para essa URL, você obterá todos os eventos que o usuário é o propietário, e que **foram criados por meio da aplicação**, juntamente com suas respectivas informações, caso ocorra um erro, será exibido o erro.


#### Retorna um evento específico
```http
  GET /api/get_task/
```
Nessa URL, na seção de `body` será necessário selecionar JSON e colocar o seguinte formato de conteúdo, no qual a string a ser inserida deverá ser o id do evento a ser acessado (que foi retornado no processo de criação da tarefa), com isso, será retornado o status da solicitação, e todas as informações do evento requisitado, se o usuário for o propietário, caso ocorra um erro, será exibido o erro. Segue o exemplo de `body`:
```json
{
    id: string
}
```

#### Deletar um evento
```http
  DELETE /api/delete/
```
Nessa URL, na seção de `body` será necessário selecionar JSON e colocar o seguinte formato de conteúdo, no qual a string referente à id deverá ser o id do evento a ser deletado (que foi retornado no processo de criação da tarefa). Caso o evento seja deletado com sucesso, será exibida uma mensagem de sucesso, caso não, será exibido o erro. 
Segue o exemplo de `body`:
```json
{
    id: string
}
```

#### Atualizar um evento
```http
  PATCH /api/update/
```
Nessa URL, na seção de `body` será necessário selecionar JSON e colocar o seguinte formato de conteúdo, no qual a string referente à id deverá ser o id do evento a ser atualizado e os campos que deseja atualizar, juntamente com os valores a serem inseridos (só é necessário passar os valores que deseja atualizar). Caso a atualização seja feita com sucesso, será exibida uma mensagem de sucesso, caso não ser´´a exibido o erro.

Segue um exemplo de `body`:
```json
{
    id: string
    ...outros campos a serem explicados a seguir
}
```

Todos os campos da tabela de criação podem ser passados da mesma forma exceto `participants` e `reminders`. Segue a explicação de cada um:

| Parâmetro   | Tipo       | Descrição                                   |
| :---------- | :--------- | :------------------------------------------ |
| `participants_add`      | Lista dos participantes a serem adicionados ((deve ser passado como uma lista com os participantes a serem inseridos) |
| `participants_del`      | Lista dos participantes a serem deletados (deve ser passado como uma lista com os participantes a serem inseridos) |
| `reminders_edit`      | Lista dos alertas a serem editados (pode ser passados da mesma forma que foram passados ao criar o evento, com a diferença que só pode ser editado o valor de `minutes`) |
| `reminders_del`      | Lista dos alertas a serem deletados (no formato: `["alerta", "alerta"]`, em que cada `alerta` é o alerta que você deseja remover) |
| `reminders_add`      | Lista dos alertas a serem adicionados (pode ser passados da mesma forma que foram passados ao criar o evento) |

Exemplos:
- Suponha que você queira editar o evento do cinema citado acima para remover a descrição, editar a data de início para 26 de setembro de 2024, remover um participante, remover a notificação por e-mail, editar a notificação por popup para 1h e remover um participante. Você terá algo como:
```json
{
    "description": "",
    "date_start": "2024-09-26",
    "participants_del":[
        "filho@email.com"
    ],
    "reminders_del": [
        "email"
    ],
    "reminders_edit": [
        {"method": "popup", "minutes": 150}
    ]
}
```



#### Buscar por um evento
```http
  GET /api/search?...<parametros>/
```
Nessa URL será necessário enviar, na própia URL, os seguinte parâmetros, os quais não são obrigatórios, mas no caso da busca ser realizada com base em mais de um parâmetro deve-se usaro separados `&`. Caso a solicitação seja feita com sucesso, serão exibidos os eventos que correspondem à sua busca, caso contrário, será exibida uma mensagem de erro:

Segue a tabela com os possíveis parâmetros.


| Parâmetro   | Descrição                                   | Formato |
| :---------- | :--------- | :------------------------------------------ |
| `q`      | String que você deseja pesquisar no título de um evento | `string` |
| `date_start`      | Intervalo no qual você deseja buscar a data de início do evento | `data_inicial_do_intervalo\|data_final_do_intervalo`
| `date_end`      | String que você deseja pesquisar no título de um evento | Intervalo no qual você deseja buscar a data de término do evento | `data_inicial_do_intervalo\|data_final_do_intervalo` |
| `locale`      | String que você deseja pesquisar no local de um evento | `string` |
| `participants`      | String que você deseja pesquisar nos participantes de um evento | `string` |

Exemplos:
- Suponha que você queira buscar um evento que tenha `cinema` no título, que se inicie no dia 17 de novembro de 2024, que tenha `Shopping` no local, e que tenha como participante `esposa`. Você terá algo como:
```http
  GET /api/search?q=cinema&date_start=2024-11-17|2024-11-17&locale=shopping&participants=esposa/
```

- Suponha que você queira buscar um evento que tenha `aula` no título, que se termine entre dia 5 de setembro de 2024 e 18 de novembro de 2025, que tenha `online` no local. Você terá algo como:
```http
  GET /api/search?q=aula&date_start=2024-09-05|2025-11-18&locale=online/
```
