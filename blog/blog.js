let articles;
const monthNames = ["January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];
let tagList = new Set();

let articleCards = [];




$.getJSON("/blog/articles.json", function (data) {
  // Read the data, hide the loading spinner and build the blog
  articles = data.articles;
  // $("#spinner").hide()
  // blogBuilder();


  for (let index = 0; index < articles.length; index++) {
    const element = articles[index];
    createBlog(element, (index +1)* 400);
  }
});

function date2string(date){
  let day = date.getDate();
  switch(day.toString().split('').pop()){
    case '1':
      day += "st";
      break;
    case '2': 
      day += "nd";
      break;
    case '3': 
      day += "rd";
      break;
    default:
      day += "th";
      break;
  }
  
  return `${day} of ${monthNames[date.getMonth()]} ${date.getFullYear()}`;
}

function replaceAll(string, selector, value){
  let rString = string;
  let pString;
  do{
    pString = rString;
    rString = rString.replace(selector, value);
  }while(pString != rString);
  return rString;
}

function createBlog (data, delay) {

    let blogTemplate =  '<div class="blog-container"><a href="!{link}!"><span class="blog-link"></span></a><div class="blog-body"><div class="blog-title"><h1><a href="!{link}!">!{headline}!</a></h1></div>        <div class="blog-summary">        <p>!{summary}!</p></div></div>    <div class="blog-footer"><ul><li class="type date">!{date}!</li>!{tags}!</ul>    </div>    </div>'
    blogTemplate = blogTemplate.replace("!{link}!", data.link);
    blogTemplate = blogTemplate.replace("!{headline}!", data.headline);
    blogTemplate = blogTemplate.replace("!{summary}!", data.summary);

    let date = new Date(data.date * 1000);
    let dateString = date2string(date);
    
    blogTemplate = blogTemplate.replace("!{date}!", dateString);

    let tags = data.tags;
    let tagTemplate = '<li class="lang !{tag}!">!{tag}!</li>'
    let tagHTML = ""
    console.log(tags)
    for (let index = 0; index < tags.length; index++) {
      let tag = tags[index].toLowerCase();
      tagList.add(tag);
      if (tag === "c++") {
         let local = tagTemplate.replace("!{tag}!", "cpp"); 
         tagHTML += local.replace("!{tag}!", "c++"); 
      }else{
        tagHTML += replaceAll(tagTemplate, "!{tag}!", tag);
      }
      
    }
    blogTemplate = blogTemplate.replace("!{tags}!", tagHTML);
    articleCards.push(blogTemplate);

    $(blogTemplate).hide().appendTo($("#blogBox")).fadeIn(delay);
    // $("#blogBox").append(blogTemplate)


};


